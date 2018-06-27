from django import forms
from django.forms.widgets import RadioChoiceInput, RadioFieldRenderer
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from cms.forms.fields import PageSelectFormField
from cms.models import Page, Title

from . import models
from .utils import get_page_url


def _get_pages_for_bulk_request(site, language):
    base_qs = (
        Page.objects
        .drafts()
        .select_related('node__parent')
        .filter(node__site=site)
        .filter(title_set__language__in=[language])
        .order_by('node__path')
    )
    ids_by_path = {}
    for page in base_qs.iterator():
        parent_node = page.node.parent
        if parent_node:
            if parent_node.path in ids_by_path:
                ids_by_path[page.node.path] = page.pk
        else:
            ids_by_path[page.node.path] = page.pk
    return base_qs.filter(pk__in=ids_by_path.values())


def _get_bulk_request_eligible_source_pages(source_language, target_language, source_site, target_site):
    source_site_qs = _get_pages_for_bulk_request(source_site, source_language)
    target_site_qs = _get_pages_for_bulk_request(target_site, target_language)
    return source_site_qs.filter(
        title_set__title__in=Title.objects.filter(
            # target site page should have translation in source language with
            # same title as source page to be able to translate it
            language=source_language,
            page__in=target_site_qs.values_list('pk', flat=True),
        ).values_list('title', flat=True),
    )


class PageTreeMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = forms.CheckboxSelectMultiple
    INDENT = 8

    def label_from_instance(self, obj):
        source_link = get_page_url(obj, self.source_language)
        target_link = get_page_url(obj, self.target_language)

        return format_html(
            '<span data-path="{path}"></span>'
            '{indent}{title} '
            '<a class="select-children">{button_label}</a>'
            '<a href="{source_link}" target="_blank">{source_language}</a>'
            '<a href="{target_link}" target="_blank">{target_language}</a>',
            path=obj.node.path,
            indent=mark_safe('&nbsp;' * (obj.node.depth - 1) * self.INDENT),
            title=obj.get_title(self.source_language),
            button_label=_('Select with children'),
            source_link=source_link,
            source_language=self.source_language,
            target_link=target_link,
            target_language=self.target_language,
        )


class CreateTranslationForm(forms.ModelForm):
    source_cms_page = PageSelectFormField()
    target_cms_page = PageSelectFormField()

    class Meta:
        model = models.TranslationRequest
        fields = [
            'source_cms_page',
            'source_language',
            'target_cms_page',
            'target_language',
            'provider_backend',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(CreateTranslationForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        super(CreateTranslationForm, self).clean(*args, **kwargs)
        if not self.is_valid():
            return

        translation_request = models.TranslationRequest(
            source_language=self.cleaned_data['source_language'],
            target_language=self.cleaned_data['target_language'],
            provider_backend=self.cleaned_data['provider_backend'],
        )

        models.TranslationRequestItem(
            translation_request=translation_request,
            source_cms_page=self.cleaned_data['source_cms_page'],
            target_cms_page=self.cleaned_data['target_cms_page'],
        ).clean()

        return self.cleaned_data

    def save(self, *args, **kwargs):
        self.instance.user = self.user
        translation_request = super(CreateTranslationForm, self).save(*args, **kwargs)

        translation_request.items.create(
            source_cms_page=self.cleaned_data['source_cms_page'],
            target_cms_page=self.cleaned_data['target_cms_page'],
        )
        translation_request.set_provider_order_name(self.cleaned_data['source_cms_page'])
        return translation_request


class TranslateInBulkStep1Form(forms.ModelForm):
    ''' Step 1: creates the <TranslationRequest> (without <TranslationRequestItem>s). '''

    class Meta:
        model = models.TranslationRequest
        fields = [
            'source_site',
            'source_language',
            'target_site',
            'target_language',
            'provider_backend',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(TranslateInBulkStep1Form, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        super(TranslateInBulkStep1Form, self).clean(*args, **kwargs)
        if not self.is_valid():
            return

        eligible_pages = _get_bulk_request_eligible_source_pages(
            self.cleaned_data['source_language'],
            self.cleaned_data['target_language'],
            self.cleaned_data['source_site'],
            self.cleaned_data['target_site'],
        )
        if not eligible_pages.exists():
            raise forms.ValidationError('No eligible pages found for this configuration.')

        return self.cleaned_data

    def save(self, *args, **kwargs):
        self.instance.user = self.user
        return super(TranslateInBulkStep1Form, self).save(*args, **kwargs)


class TranslateInBulkStep2Form(forms.Form):
    ''' Step 2: adds <TranslationRequestItem>s to <TranslationRequest> created on Step 1. '''

    pages = PageTreeMultipleChoiceField(Page.objects.drafts())

    def __init__(self, *args, **kwargs):
        self.translation_request = kwargs.pop('translation_request')
        super(TranslateInBulkStep2Form, self).__init__(*args, **kwargs)

        pages_field = self.fields['pages']
        pages_field.source_language = self.translation_request.source_language
        pages_field.target_language = self.translation_request.target_language
        pages_field.queryset = (
            _get_bulk_request_eligible_source_pages(
                pages_field.source_language,
                pages_field.target_language,
                self.translation_request.source_site,
                self.translation_request.target_site,
            )
            .order_by('node__path')
            .select_related('node__site')
        )

    def save(self, *args, **kwargs):
        target_site_qs = _get_pages_for_bulk_request(
            self.translation_request.target_site,
            self.translation_request.target_language,
        )
        page_pairs = [
            (
                source_page,
                target_site_qs.filter(
                    title_set__title__in=source_page.title_set.filter(
                        language=self.translation_request.source_language,
                    ).values_list('title', flat=True)
                ).first(),
            )
            for source_page in self.cleaned_data['pages']
        ]
        translation_request_items = [
            models.TranslationRequestItem(
                source_cms_page=source_page,
                target_cms_page=target_page,
                translation_request=self.translation_request
            )
            for source_page, target_page in page_pairs
            if source_page and target_page
        ]
        models.TranslationRequestItem.objects.bulk_create(translation_request_items)
        self.translation_request.set_provider_order_name(self.cleaned_data['pages'][0])


class TranslateInBulkStep3Form(forms.Form):
    '''Step 3: Only for send without quote option'''

    order_type = forms.ChoiceField(widget=forms.RadioSelect)
    delivery_time = forms.ChoiceField(widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        self.translation_request = kwargs.pop('translation_request')
        super(TranslateInBulkStep3Form, self).__init__(*args, **kwargs)
        self.fields['order_type'].choices = self.translation_request.provider.get_order_type_choices()
        self.fields['delivery_time'].choices = self.translation_request.provider.get_delivery_time_choices()

    def save(self, *args, **kwargs):
        self.translation_request.set_content_from_cms()
        self.translation_request.set_request_content()
        self.translation_request.set_provider_options(
            order_type=self.cleaned_data['order_type'],
            delivery_time=self.cleaned_data['delivery_time'],
            additional_info='Order without Quote',
        )
        self.translation_request.set_status(models.TranslationRequest.STATES.READY_FOR_SUBMISSION)
        self.translation_request.submit_request()


class QuoteInput(RadioChoiceInput):
    def __init__(self, *args, **kwargs):
        super(QuoteInput, self).__init__(*args, **kwargs)
        self.choice_label = mark_safe('<strong>oy</strong>')
        obj = models.TranslationQuote.objects.get(pk=self.choice_value)
        self.choice_label = mark_safe(
            '<strong>{}</strong><br>'
            '{}<br><br>'
            'Delivery until: {}<br>'
            'Price: {} {}'
            .format(obj.name, obj.description, obj.delivery_date, obj.price_currency, obj.price_amount)
        )


class QuoteRenderer(RadioFieldRenderer):
    choice_input_class = QuoteInput


class QuoteWidget(forms.RadioSelect):
    renderer = QuoteRenderer


class ChooseTranslationQuoteForm(forms.ModelForm):
    class Meta:
        model = models.TranslationRequest
        fields = (
            'selected_quote',
        )
        widgets = {
            'selected_quote': QuoteWidget(),
        }

    def __init__(self, *args, **kwargs):
        super(ChooseTranslationQuoteForm, self).__init__(*args, **kwargs)
        self.fields['selected_quote'].required = True
        self.fields['selected_quote'].queryset = self.instance.quotes.all()
        self.fields['selected_quote'].empty_label = None
