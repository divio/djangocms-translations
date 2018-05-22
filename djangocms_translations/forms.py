from django.conf import settings
from django import forms
from django.forms.widgets import RadioFieldRenderer, RadioChoiceInput
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from cms.forms.fields import PageSelectFormField
from cms.models import Page

from . import models


def _get_bulk_request_eligible_pages(source_language, target_language):
    return (
        Page.objects
        .drafts()
        .filter(node__site=settings.SITE_ID)
        .filter(title_set__language__in=[source_language])
        .filter(title_set__language__in=[target_language])
    )


class PageTreeMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = forms.CheckboxSelectMultiple
    INDENT = 8

    def label_from_instance(self, obj):
        source_link = obj.get_absolute_url(self.source_language)
        target_link = obj.get_absolute_url(self.target_language)

        return format_html(
            '<span data-path="{path}"></span>'
            '{indent}{obj} '
            '<a class="select-children">{button_label}</a>'
            '<a href="{source_link}" target="_blank">{source_language}</a>'
            '<a href="{target_link}" target="_blank">{target_language}</a>',
            path=obj.node.path,
            indent=mark_safe('&nbsp;' * (obj.node.depth - 1) * self.INDENT),
            obj=obj,
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

        return translation_request


class TranslateInBulkStep1Form(forms.ModelForm):
    ''' Step 1: creates the <TranslationRequest> (without <TranslationRequestItem>s). '''

    class Meta:
        model = models.TranslationRequest
        fields = [
            'source_language',
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

        eligible_pages = _get_bulk_request_eligible_pages(
            self.cleaned_data['source_language'], self.cleaned_data['target_language']
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
            _get_bulk_request_eligible_pages(pages_field.source_language, pages_field.target_language)
            .order_by('node__path')
            .select_related('node')
        )

    def save(self, *args, **kwargs):
        translation_request_items = [
            models.TranslationRequestItem(
                source_cms_page=page,
                target_cms_page=page,
                translation_request=self.translation_request
            )
            for page in self.cleaned_data['pages']
        ]
        models.TranslationRequestItem.objects.bulk_create(translation_request_items)


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
