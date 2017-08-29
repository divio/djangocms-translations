# -*- coding: utf-8 -*-
import json

from django.conf.urls import url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import ManyToOneRel
from django.utils.safestring import mark_safe
from django.utils.translation import get_language_info, ugettext_lazy as _

from djangocms_translations.utils import pretty_json
from . import models, views


class AllReadOnlyFieldsMixin(object):
    def get_readonly_fields(self, request, obj=None):
        return [
            field.name for field in self.model._meta.get_fields()
            if not isinstance(field, ManyToOneRel)
        ] + list(self.readonly_fields)


class TranslationQuoteInline(AllReadOnlyFieldsMixin, admin.TabularInline):
    model = models.TranslationQuote
    extra = 0


class TranslationOrderInline(AllReadOnlyFieldsMixin, admin.StackedInline):
    model = models.TranslationOrder
    extra = 0

    fields = (
        (
            'date_created',
            'date_translated',
        ),
        'state',
        'pretty_provider_options',
        'pretty_request_content',
        'pretty_response_content',
    )

    readonly_fields = (
        'pretty_provider_options',
        'pretty_request_content',
        'pretty_response_content',
    )

    def pretty_provider_options(self, obj):
        return pretty_json(json.dumps(obj.provider_options))
    pretty_provider_options.short_description = _('Provider options')

    def pretty_request_content(self, obj):
        return pretty_json(json.dumps(obj.request_content))
    pretty_request_content.short_description = _('Request content')

    def pretty_response_content(self, obj):
        return pretty_json(json.dumps(obj.response_content))
    pretty_response_content.short_description = _('Response content')


@admin.register(models.TranslationRequest)
class TranslationRequestAdmin(AllReadOnlyFieldsMixin, admin.ModelAdmin):
    inlines = [
        TranslationQuoteInline,
        TranslationOrderInline,
    ]

    list_display = (
        'date_created',
        'pretty_cms_page',
        'pretty_source_language',
        'pretty_target_language',
        'status',
        'action',
    )

    fields = (
        'user',
        'state',
        (
            'date_created',
            'date_submitted',
            'date_received',
            'date_imported',
        ),
        'pretty_cms_page',
        (
            'pretty_source_language',
            'pretty_target_language',
        ),
        'provider_backend',
        'pretty_provider_options',
        'pretty_export_content',
        'pretty_request_content',
        'selected_quote',
    )

    readonly_fields = (
        'date_created',
        'date_submitted',
        'date_received',
        'date_imported',
        'pretty_cms_page',
        'pretty_source_language',
        'pretty_target_language',
        'pretty_provider_options',
        'pretty_export_content',
        'pretty_request_content',
        'selected_quote',
    )

    def pretty_cms_page(self, obj):
        return mark_safe(
            '<a href="{}" target="_parent">{}</a>'.format(
                obj.cms_page.get_absolute_url(),
                obj.cms_page,
            )
        )
    pretty_cms_page.short_description = _('CMS Page')

    def _get_language_info(self, lang_code):
        return get_language_info(lang_code)['name']

    def pretty_source_language(self, obj):
        return self._get_language_info(obj.source_language)
    pretty_source_language.short_description = _('Source language')

    def pretty_target_language(self, obj):
        return self._get_language_info(obj.target_language)
    pretty_target_language.short_description = _('Target language')

    def pretty_provider_options(self, obj):
        return pretty_json(json.dumps(obj.provider_options))
    pretty_provider_options.short_description = _('Provider options')

    def pretty_export_content(self, obj):
        return pretty_json(obj.export_content)
    pretty_export_content.short_description = _('Export content')

    def pretty_request_content(self, obj):
        return pretty_json(json.dumps(obj.request_content))
    pretty_request_content.short_description = _('Request content')

    def action(self, obj):
        def render_action(url, title):
            return mark_safe(
                '<a href="{url}">{title}</a>'
                .format(url=url, title=title)
            )
        if obj.state == models.TranslationRequest.STATES.PENDING_APPROVAL:
            return render_action(
                reverse('admin:choose-translation-quote', args=(obj.pk,)),
                _('Choose quote'),
            )
        elif obj.state == models.TranslationRequest.STATES.IN_TRANSLATION:
            return render_action(
                reverse('admin:translation-request-check-status', args=(obj.pk,)),
                _('Check Status'),
            )
        elif obj.state == models.TranslationRequest.STATES.READY_FOR_IMPORT:
            return render_action(
                reverse('admin:translation-request-import-response', args=(obj.pk,)),
                _('Import response'),
            )

    def get_urls(self):
        return [
            url(
                r'add/$',
                views.CreateTranslationRequestView.as_view(),
                name='create-translation-request',
            ),
            url(
                r'(?P<pk>\w+)/choose-quote/$',
                views.ChooseTranslationQuoteView.as_view(),
                name='choose-translation-quote',
            ),
            url(
                r'(?P<pk>\w+)/check-status/$',
                views.CheckRequestStatusView.as_view(),
                name='translation-request-check-status',
            ),
            url(
                r'(?P<pk>\w+)/callback/$',
                views.TranslationRequestProviderCallbackView.as_view(),
                name='translation-request-provider-callback',
            ),
            url(
                r'(?P<pk>\w+)/import-response/$',
                views.ImportProviderResponse.as_view(),
                name='translation-request-import-response',
            ),

            # has to be the last one
            url(
                r'(?P<pk>\w+)/aa$',
                views.TranslationRequestStatusView.as_view(),
                name='translation-request-detail',
            ),
        ] + super(TranslationRequestAdmin, self).get_urls()
