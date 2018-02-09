from django import forms
from cms.forms.fields import PageSelectFormField
from django.forms.widgets import RadioFieldRenderer, RadioChoiceInput
from django.utils.safestring import mark_safe

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
        translation_request_data = self.cleaned_data.copy()
        self.translation_request_item_data = {
            'source_cms_page': translation_request_data.pop('source_cms_page', None),
            'target_cms_page': translation_request_data.pop('target_cms_page', None),
        }

        translation_request = models.TranslationRequest(**translation_request_data)
        translation_request.clean()

        self.translation_request_item_data['translation_request'] = translation_request
        translation_request_item = models.TranslationRequestItem(**self.translation_request_item_data)
        translation_request_item.clean()

        return super(CreateTranslationForm, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.user = self.user
        translation_request = super(CreateTranslationForm, self).save(*args, **kwargs)

        del self.translation_request_item_data['translation_request']
        translation_request.translation_request_items.create(**self.translation_request_item_data)

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
