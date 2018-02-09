from django.conf import settings
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioFieldRenderer, RadioChoiceInput
from django.utils.safestring import mark_safe
from cms.forms.fields import PageSelectFormField
from cms.models import Page

from . import conf
from . import models

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
        translation_request_data = self.cleaned_data.copy()
        self.translation_request_item_data = {
            'source_cms_page': translation_request_data.pop('source_cms_page', None),
            'target_cms_page': translation_request_data.pop('target_cms_page', None),
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


class BulkCreateTranslationForm(forms.ModelForm):
    # FIXME: <CMS3.5 compat?
    # FIXME: Only draft/non draft?
    pages = forms.ModelMultipleChoiceField(Page.objects.drafts().filter(node__site=settings.SITE_ID))

    class Meta:
        model = models.TranslationRequest
        fields = [
            'pages',
            'source_language',
            'target_language',
            'provider_backend',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(BulkCreateTranslationForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        super(BulkCreateTranslationForm, self).clean(*args, **kwargs)
        translation_request_data = self.cleaned_data.copy()
        pages = translation_request_data.pop('pages')
        translation_request = models.TranslationRequest(**translation_request_data)

        if len(pages) > conf.TRANSLATIONS_MAX_PAGES_PER_BULK:
            message = (
                'Bulk requests may contain up to {} pages (you selected {})'
                .format(conf.TRANSLATIONS_MAX_PAGES_PER_BULK, len(pages))
            )
            raise ValidationError({'pages': message})

        for page in pages:
            translation_request_item = models.TranslationRequestItem(
                translation_request=translation_request,
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
        self.instance.user = self.user
        translation_request = super(BulkCreateTranslationForm, self).save(*args, **kwargs)

        pages = self.cleaned_data['pages']
        for page in pages:
            translation_request.translation_request_items.create(source_cms_page=page, target_cms_page=page)

        return translation_request


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
