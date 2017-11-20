from django import forms
from django.forms import Select
from django.forms.widgets import RadioFieldRenderer, RadioChoiceInput
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from cms.models import Page

from .utils import get_languages_for_current_site
from . import models


class CreateTranslationForm(forms.ModelForm):
    cms_page = forms.ModelChoiceField(
        queryset=Page.objects.drafts(),
        widget=forms.widgets.HiddenInput(),
    )

    class Meta:
        model = models.TranslationRequest
        fields = [
            'cms_page',
            'provider_backend',
            'source_language',
            'target_language',
        ]

        widgets = {
            'source_language': Select,
            'target_language': Select,
        }

    def __init__(self, *args, **kwargs):
        super(CreateTranslationForm, self).__init__(*args, **kwargs)
        self.fields['provider_backend'].choices = self.fields['provider_backend'].choices[1:]
        for field in ('source_language', 'target_language'):
            self.fields[field] = forms.ChoiceField(choices=self.build_language_choices())

    @cached_property
    def selected_page(self):
        if self.is_valid():
            data = self.cleaned_data
        else:
            data = self.data or self.initial

        if data.get('cms_page'):
            return Page.objects.drafts().get(pk=data['cms_page'])

    def build_language_choices(self):
        return [
            (lang['code'], _(lang['name']))
            for lang in get_languages_for_current_site()
        ]

    def save(self, commit=True):
        self.instance.user = self.initial['user']
        return super(CreateTranslationForm, self).save(commit)


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
