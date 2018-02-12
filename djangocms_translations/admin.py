# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import ManyToOneRel
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import get_language_info, ugettext_lazy as _

from cms.admin.placeholderadmin import PlaceholderAdminMixin
from cms.models import CMSPlugin
from cms.operations import ADD_PLUGIN
from cms.plugin_pool import plugin_pool

from . import models, views
from .utils import get_plugin_form, pretty_json


class AllReadOnlyFieldsMixin(object):
    def get_readonly_fields(self, request, obj=None):
        return [
            field.name for field in self.model._meta.get_fields()
            if not isinstance(field, ManyToOneRel)
        ] + list(self.readonly_fields)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class TranslationRequestItemInline(AllReadOnlyFieldsMixin, admin.TabularInline):
    model = models.TranslationRequestItem
    extra = 0

    readonly_fields = (
        'pretty_source_cms_page',
        'pretty_target_cms_page',
    )
    fields = readonly_fields

    def _pretty_page_display(self, page):
        return mark_safe('<a href="{}" target="_parent">{}</a>'.format(page.get_absolute_url(), page))

    def pretty_source_cms_page(self, obj):
        return self._pretty_page_display(obj.source_cms_page)
    pretty_source_cms_page.short_description = _('Source CMS Page')

    def pretty_target_cms_page(self, obj):
        return self._pretty_page_display(obj.target_cms_page)
    pretty_target_cms_page.short_description = _('Target CMS Page')


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
        return pretty_json(obj.provider_options)
    pretty_provider_options.short_description = _('Provider options')

    def pretty_request_content(self, obj):
        return pretty_json(obj.request_content)
    pretty_request_content.short_description = _('Request content')

    def pretty_response_content(self, obj):
        return pretty_json(obj.response_content)
    pretty_response_content.short_description = _('Response content')


@admin.register(models.TranslationRequest)
class TranslationRequestAdmin(AllReadOnlyFieldsMixin, admin.ModelAdmin):
    inlines = [
        TranslationRequestItemInline,
        TranslationQuoteInline,
        TranslationOrderInline,
    ]

    list_filter = ('state',)
    list_display = (
        'date_created',
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
        'pretty_source_language',
        'pretty_target_language',
        'pretty_provider_options',
        'pretty_export_content',
        'pretty_request_content',
        'selected_quote',
    )

    def _get_language_info(self, lang_code):
        return get_language_info(lang_code)['name']

    def pretty_source_language(self, obj):
        return self._get_language_info(obj.source_language)
    pretty_source_language.short_description = _('Source language')

    def pretty_target_language(self, obj):
        return self._get_language_info(obj.target_language)
    pretty_target_language.short_description = _('Target language')

    def pretty_provider_options(self, obj):
        return pretty_json(obj.provider_options)
    pretty_provider_options.short_description = _('Provider options')

    def pretty_export_content(self, obj):
        return pretty_json(obj.export_content)
    pretty_export_content.short_description = _('Export content')

    def pretty_request_content(self, obj):
        return pretty_json(obj.request_content)
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

    def get_urls(self):
        return [
            url(
                r'bulk-add/$',
                views.BulkCreateTranslationRequestView.as_view(),
                name='bulk-create-translation-request',
            ),
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
                views.process_provider_callback_view,
                name='translation-request-provider-callback',
            ),
            url(
                r'(?P<pk>\w+)/adjust-import-data/$',
                views.adjust_import_data_view,
                name='translation-request-adjust-import-data',
            ),
            url(
                r'(?P<pk>\w+)/import-from-archive/$',
                views.import_from_archive,
                name='translation-request-import-from-archive',
            ),

            # has to be the last one
            url(
                r'(?P<pk>\w+)/aa$',
                views.TranslationRequestStatusView.as_view(),
                name='translation-request-detail',
            ),
        ] + super(TranslationRequestAdmin, self).get_urls()


@admin.register(models.ArchivedPlaceholder)
class ArchivedPlaceholderAdmin(PlaceholderAdminMixin, admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def _get_plugin_from_id(self, plugin_id):
        queryset = (
            CMSPlugin
            .objects
            .select_related('placeholder', 'trans_archived_plugin')
        )
        return get_object_or_404(queryset, pk=plugin_id)

    def add_plugin(self, request):
        if 'plugin' not in request.GET:
            return super(ArchivedPlaceholderAdmin, self).add_plugin(request)

        plugin = self._get_plugin_from_id(request.GET['plugin'])
        archived_plugin = plugin.trans_archived_plugin
        plugin_class = plugin_pool.get_plugin(plugin.plugin_type)
        plugin_instance = plugin_class(plugin_class.model, self.admin_site)

        # Let django clean the data and provide us with valid initial data.
        # This addresses an issue where certain fields expect relationships
        # to exist even if the value is just initial data.
        form_data = archived_plugin.data.copy()
        plugin_form = get_plugin_form(plugin.plugin_type, data=form_data)
        plugin_form.full_clean()

        for field in list(form_data.keys()):
            if not plugin_form.cleaned_data.get(field):
                del form_data[field]

        # Setting attributes on the form class is perfectly fine.
        # The form class is created by modelform factory every time
        # this get_form() method is called.
        plugin_instance._cms_initial_attributes = {
            'id': plugin.pk,
            'language': plugin.language,
            'placeholder': plugin.placeholder,
            'parent': plugin.parent,
            'plugin_type': plugin.plugin_type,
            'position': plugin.position,
        }
        plugin_instance.get_changeform_initial_data = lambda self: form_data

        response = plugin_instance.add_view(request)

        plugin = getattr(plugin_instance, 'saved_object', None)

        if plugin_instance._operation_token:
            placeholder = plugin.placeholder
            tree_order = placeholder.get_plugin_tree_order(plugin.parent_id)
            self._send_post_placeholder_operation(
                request,
                operation=ADD_PLUGIN,
                token=plugin_instance._operation_token,
                plugin=plugin,
                placeholder=plugin.placeholder,
                tree_order=tree_order,
            )
        return response

    def edit_plugin(self, request, plugin_id):
        try:
            plugin_id = int(plugin_id)
        except ValueError:
            return HttpResponseNotFound(force_text(_("Plugin not found")))

        obj = self._get_plugin_from_id(plugin_id)
        plugin_class = plugin_pool.get_plugin(obj.plugin_type)
        plugin_lookup = plugin_class.get_render_queryset().filter(pk=obj.pk)

        if plugin_lookup.exists():
            return super(ArchivedPlaceholderAdmin, self).edit_plugin(request, plugin_id)

        query = request.GET.copy()
        query['plugin'] = plugin_id
        return redirect('{}?{}'.format(obj.get_add_url(), query.urlencode()))


from functools import partial
from cms.models import CMSPlugin, Page
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from .forms import BulkCreateTranslationForm
from .models import TranslationRequest
from .tasks import prepare_translation_bulk_request


class BulkTranslationPage(Page):
    class Meta:
        proxy = True
        verbose_name = 'Page for bulk translation'
        verbose_name_plural = 'Pages for bulk translation'


@admin.register(BulkTranslationPage)
class BulkTranslationPageAdmin(admin.ModelAdmin):
    list_display = ('pretty_title', )
    INDENT = 4

    def get_queryset(self, request):
        return (
            Page.objects.
            drafts().
            filter(node__site=settings.SITE_ID)
            .order_by('node__path')
            .select_related('node')
        )

    def pretty_title(self, item):
        return '{}{}'.format('&nbsp;' * (item.node.depth - 1) * self.INDENT, item)
    pretty_title.short_description = _('title')
    pretty_title.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = {}
        languages = settings.LANGUAGES
        providers = TranslationRequest.PROVIDERS

        for source_language, source_language_label in languages:
            for target_language, target_language_label in languages:
                if source_language == target_language:
                    continue

                for provider, provider_label in providers:
                    data = {
                        'source_language': source_language,
                        'target_language': target_language,
                        'provider_backend': provider
                    }
                    action_method = partial(self.bulk_translation, data=data)
                    action_identifier = 'bulk_{}_{}_{}'.format(source_language, target_language, provider)
                    action_label = _(
                        'Bulk translate via {} ({} --> {})'
                    ).format(provider_label, source_language_label, target_language_label)
                    actions[action_identifier] = (action_method, action_identifier, action_label)

        return actions

    def bulk_translation(self, modeladmin, request, queryset, data):
        data['pages'] = list(queryset.values_list('id', flat=True))
        form = BulkCreateTranslationForm(data=data, user=request.user)

        if form.is_valid():
            translation_request = form.save()
            prepare_translation_bulk_request.delay(translation_request.id)
            message = 'Bulk is being processed in background. Please check the status in a few moments.'
            self.message_user(request, message)
            return redirect(reverse('admin:djangocms_translations_translationrequest_changelist'))

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    self.message_user(request, '{}: {}'.format(field, error), level=messages.ERROR)
