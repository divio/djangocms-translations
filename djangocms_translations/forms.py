from django.conf import settings
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioFieldRenderer, RadioChoiceInput
from django.utils.safestring import mark_safe
from cms.forms.fields import PageSelectFormField
from cms.models import Page

from . import conf
from . import models


class PageTreeMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = forms.CheckboxSelectMultiple
    INDENT = 8

    def label_from_instance(self, obj):
        return mark_safe('{}{}'.format('&nbsp;' * (obj.node.depth - 1) * self.INDENT, obj))


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

        translation_request_data = self.cleaned_data.copy()
        self.translation_request_item_data = {
            'source_cms_page': translation_request_data.pop('source_cms_page'),
            'target_cms_page': translation_request_data.pop('target_cms_page'),
        }
        translation_request = models.TranslationRequest(**translation_request_data)

        self.translation_request_item_data['translation_request'] = translation_request
        translation_request_item = models.TranslationRequestItem(**self.translation_request_item_data)
        translation_request_item.clean()

        return self.cleaned_data

    def save(self, *args, **kwargs):
        self.instance.user = self.user
        translation_request = super(CreateTranslationForm, self).save(*args, **kwargs)

        del self.translation_request_item_data['translation_request']
        translation_request.translation_request_items.create(**self.translation_request_item_data)

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

    def save(self, *args, **kwargs):
        self.instance.user = self.user
        return super(TranslateInBulkStep1Form, self).save(*args, **kwargs)


class TranslateInBulkStep2Form(forms.Form):
    ''' Step 2: adds <TranslationRequestItem>s to <TranslationRequest> created on Step 1. '''

    pages = PageTreeMultipleChoiceField(Page.objects.drafts())

    def __init__(self, *args, **kwargs):
        self.translation_request = kwargs.pop('translation_request')
        super(TranslateInBulkStep2Form, self).__init__(*args, **kwargs)

        self.fields['pages'].queryset = (
            self.fields['pages'].queryset
            .filter(node__site=settings.SITE_ID)
            .filter(title_set__language__in=[self.translation_request.source_language])
            .filter(title_set__language__in=[self.translation_request.target_language])
            .order_by('node__path')
            .select_related('node')
        )

    def clean(self, *args, **kwargs):
        super(TranslateInBulkStep2Form, self).clean(*args, **kwargs)
        if not self.is_valid():
            return

        pages = self.cleaned_data['pages']

        if len(pages) > conf.TRANSLATIONS_MAX_PAGES_PER_BULK:
            message = (
                'Bulk requests may contain up to {} pages (you selected {})'
                .format(conf.TRANSLATIONS_MAX_PAGES_PER_BULK, len(pages))
            )
            raise ValidationError({'pages': message})

        for page in pages:
            translation_request_item = models.TranslationRequestItem(
                translation_request=self.translation_request,
                source_cms_page=page,
                target_cms_page=page,
            )
            try:
                translation_request_item.clean()
            except ValidationError as e:
                enriched_error_message = ['{}: {}'.format(str(page), m) for m in list(e.message_dict.values())[0]]
                raise ValidationError({'pages': enriched_error_message})

        return self.cleaned_data

    def save(self, *args, **kwargs):
        pages = self.cleaned_data['pages']
        for page in pages:
            self.translation_request.translation_request_items.create(source_cms_page=page, target_cms_page=page)


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
