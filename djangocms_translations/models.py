from __future__ import unicode_literals

import json
import logging

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
# from django.db.models.fields.related_descriptors import RelatedObjectDoesNotExist
from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from cms.models.fields import PageField, PlaceholderField
from cms.utils.plugins import copy_plugins_to_placeholder

from extended_choices import Choices
from djangocms_transfer.exporter import get_page_export_data
from djangocms_transfer.importer import import_plugins_to_page
from djangocms_transfer.utils import get_plugin_class

from .providers import SupertextTranslationProvider, TRANSLATION_PROVIDERS
from .utils import get_plugin_form, get_languages_for_current_site


logger = logging.getLogger('djangocms_translations')


def _get_placeholder_slot(archived_placeholder):
    return archived_placeholder.slot


def language_choices():
    return [
        (lang['code'], _(lang['name']))
        for lang in get_languages_for_current_site()
    ]


class TranslationRequest(models.Model):
    STATES = Choices(
        ('DRAFT', 'draft', _('Draft')),
        ('OPEN', 'open', _('Open')),
        ('PENDING_QUOTE', 'pending_quote', _('Pending quote from provider')),
        ('PENDING_APPROVAL', 'pending_approval', _('Pending approval of quote')),
        ('READY_FOR_SUBMISSION', 'ready_for_submission', _('Pending submission to translation provider')),
        ('IN_TRANSLATION', 'in_translation', _('In translation')),
        ('IMPORT_STARTED', 'import_started', _('Import Started')),
        ('IMPORT_FAILED', 'import_failed', _('Import Failed')),
        ('IMPORTED', 'imported', _('Imported')),
        ('CANCELLED', 'cancelled', _('Cancelled')),
    )

    PROVIDERS = Choices(
        ('SUPERTEXT', SupertextTranslationProvider.__name__, _('Supertext')),
    )

    user = models.ForeignKey(User)
    state = models.CharField(choices=STATES, default=STATES.DRAFT, max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)
    date_submitted = models.DateTimeField(blank=True, null=True)
    date_received = models.DateTimeField(blank=True, null=True)
    date_imported = models.DateTimeField(blank=True, null=True)
    source_cms_page = PageField(related_name='translation_requests_as_source', on_delete=models.CASCADE)
    source_language = models.CharField(max_length=10, choices=language_choices())
    target_cms_page = PageField(related_name='translation_requests_as_target', on_delete=models.CASCADE)
    target_language = models.CharField(max_length=10, choices=language_choices())
    provider_backend = models.CharField(max_length=100, choices=PROVIDERS)
    provider_options = JSONField(default={}, blank=True)
    export_content = JSONField(default={}, blank=True)
    request_content = JSONField(default={}, blank=True)
    selected_quote = models.ForeignKey('TranslationQuote', blank=True, null=True)

    @property
    def status(self):
        return self.STATES.for_value(self.state).display

    @property
    def provider(self):
        if not self._provider and self.provider_backend:
            self._provider = TRANSLATION_PROVIDERS.get(self.provider_backend)(self)
        return self._provider
    _provider = None

    def set_status(self, status, commit=True):
        if status not in self.STATES.values:
            raise RuntimeError('Invalid status')
        self.state = status

        if commit:
            self.save(update_fields=('state',))
        return not status == self.STATES.IMPORT_FAILED

    def export_content_from_cms(self):
        if not self.source_cms_page and not self.source_language:
            raise RuntimeError('Set a cms page and language for export')

        export_data = get_page_export_data(self.source_cms_page, self.source_language)
        self.export_content = json.dumps(export_data, cls=DjangoJSONEncoder)
        self.save(update_fields=('export_content',))
        self.set_status(self.STATES.OPEN)

    def get_quote_from_provider(self):
        self.set_status(self.STATES.PENDING_QUOTE)

        provider_quote = self.provider.get_quote()

        currency = provider_quote['Currency']
        date_received = timezone.now()
        quotes = []

        for option in provider_quote['Options']:
            order_type_id = option['OrderTypeId']
            name = '{} ({})'.format(option['Name'], option['ShortDescription'])
            description = option['Description']

            for delivery_option in option['DeliveryOptions']:
                quote = self.add_quote(
                    provider_options={
                        'OrderTypeId': order_type_id,
                        'DeliveryId': delivery_option['DeliveryId'],
                    },
                    name=name,
                    description=description,
                    delivery_date=delivery_option['DeliveryDate'],
                    price_currency=currency,
                    price_amount=delivery_option['Price'] or 0,
                    date_received=date_received,
                )
                quotes.append(quote)

        self.set_status(self.STATES.PENDING_APPROVAL)

        return quotes

    def add_quote(self, **kwargs):
        return TranslationQuote.objects.create(request=self, **kwargs)

    def submit_request(self):
        response = self.provider.send_request()
        self.set_status(self.STATES.IN_TRANSLATION)
        return response

    def check_status(self):
        if not hasattr(self, 'order'):
            return RuntimeError('Cannot check status if there is no order.')
        status = self.provider.check_status()
        self.order.state = status['Status'].lower()
        # TODO: which states are available?
        # on success, update the requests status as well
        self.order.save(update_fields=('state',))

    def import_response(self, raw_data):
        self.set_status(self.STATES.IMPORT_STARTED)
        self.order.response_content = raw_data.decode('utf-8')
        self.order.save(update_fields=('response_content',))

        try:
            placeholders = self.provider.get_import_data()
        except ValueError:
            logger.exception("Received invalid data from {}".format(self.provider_backend))
            return self.set_status(self.STATES.IMPORT_FAILED)

        try:
            import_plugins_to_page(
                placeholders=placeholders,
                page=self.target_cms_page,
                language=self.target_language
            )
        except (IntegrityError, ObjectDoesNotExist):
            self._set_import_archive()
            logger.exception("Failed to import plugins from {}".format(self.provider_backend))
            return self.set_status(self.STATES.IMPORT_FAILED)

        self.set_status(self.STATES.IMPORTED, commit=False)
        self.date_imported = timezone.now()
        self.save(update_fields=('date_imported', 'state'))
        return True

    def can_import_from_archive(self):
        if self.state == self.STATES.IMPORT_FAILED:
            return self.archived_placeholders.exists()
        return False

    @transaction.atomic
    def _import_from_archive(self):
        plugins_by_placeholder = {
            pl.slot: pl.get_plugins()
            for pl in self.archived_placeholders.all()
        }
        page_placeholders = (
            self
            .target_cms_page
            .placeholders
            .filter(slot__in=plugins_by_placeholder)
        )

        for placeholder in page_placeholders:
            plugins = plugins_by_placeholder[placeholder.slot]
            copy_plugins_to_placeholder(
                plugins=plugins,
                placeholder=placeholder,
                language=self.target_language,
            )

        self.set_status(self.STATES.IMPORTED, commit=False)
        self.date_imported = timezone.now()
        self.save(update_fields=('date_imported', 'state'))

    @transaction.atomic
    def _set_import_archive(self):
        page_placeholders = self.source_cms_page.get_declared_placeholders()
        plugins_by_placeholder = {
            pl.slot: pl.plugins
            for pl in self.provider.get_import_data() if pl.plugins
        }

        for pos, placeholder in enumerate(page_placeholders, start=1):
            if placeholder.slot not in plugins_by_placeholder:
                continue

            plugins = plugins_by_placeholder[placeholder.slot]
            bound_plugins = (plugin for plugin in plugins if plugin.data)
            ar_placeholder = (
                self
                .archived_placeholders
                .create(slot=placeholder.slot, position=pos)
            )

            try:
                ar_placeholder._import_plugins(bound_plugins)
            except (IntegrityError, ObjectDoesNotExist):
                return False

    def clean(self):
        def _get_language_labels(languages):
            language_choices_dict = dict(language_choices())
            language_labels = [language_choices_dict[lang] for lang in languages]
            return '"{}".'.format('", "'.join(map(str, language_labels)))

        self.clean_fields()

        for field_prefix in ('source', 'target'):
            page_field_name = '{}_cms_page'.format(field_prefix)
            page = getattr(self, page_field_name)
            page_languages = page.languages.split(',')
            language_field_name = '{}_language'.format(field_prefix)
            language = getattr(self, language_field_name)

            if language not in page_languages:
                raise ValidationError({
                    language_field_name:
                    _('Invalid choice. Valid choices are {}').format(_get_language_labels(page_languages))
                })

        return super(TranslationRequest, self).clean()


class TranslationQuote(models.Model):
    request = models.ForeignKey(TranslationRequest, related_name='quotes')
    date_received = models.DateTimeField()

    name = models.CharField(max_length=1000)
    description = models.TextField(blank=True, default='')
    delivery_date = models.DateTimeField(blank=True, null=True)

    price_currency = models.CharField(max_length=10)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider_options = JSONField(default={}, blank=True)

    def __str__(self):
        return '{} {} {}'.format(self.name, self.description, self.price_amount)


class TranslationOrder(models.Model):
    STATES = Choices(
        ('OPEN', 'open', _('Open')),
        ('PENDING', 'pending_quote', _('Pending')),
        ('FAILED', 'failed', _('Failed/cancelled.')),
        ('DONE', 'done', _('Done')),
    )

    request = models.OneToOneField(TranslationRequest, related_name='order')

    date_created = models.DateTimeField(auto_now_add=True)
    date_translated = models.DateTimeField(blank=True, null=True)

    state = models.CharField(choices=STATES, default=STATES.OPEN, max_length=100)

    request_content = JSONField(default={}, blank=True)
    response_content = JSONField(default={}, blank=True)

    provider_details = JSONField(default={}, blank=True)


class ArchivedPlaceholder(models.Model):
    slot = models.CharField(max_length=255)
    request = models.ForeignKey(
        TranslationRequest,
        on_delete=models.CASCADE,
        related_name='archived_placeholders',
    )
    placeholder = PlaceholderField(
        _get_placeholder_slot,
        related_name='archived_placeholders',
    )
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ('position',)
        default_permissions = ''

    def get_plugins(self):
        return self.placeholder.get_plugins()

    def _import_plugins(self, plugins):
        source_map = {}
        new_plugins = []

        for archived_plugin in plugins:
            if archived_plugin.parent_id:
                parent = source_map[archived_plugin.parent_id]
            else:
                parent = None

            if parent and parent.__class__ != CMSPlugin:
                parent = parent.cmsplugin_ptr

            plugin_form = get_plugin_form(
                archived_plugin.plugin_type,
                data=archived_plugin.data,
            )
            data_is_valid = plugin_form.is_valid()

            plugin = archived_plugin.restore(
                placeholder=self.placeholder,
                language=self.request.target_language,
                parent=parent,
                with_data=data_is_valid,
            )

            if data_is_valid:
                new_plugins.append(plugin)
            else:
                self.archived_plugins.create(
                    data=archived_plugin.data,
                    cms_plugin=plugin,
                    old_plugin_id=archived_plugin.pk,
                )
            source_map[archived_plugin.pk] = plugin

        for new_plugin in new_plugins:
            plugin_class = get_plugin_class(new_plugin.plugin_type)

            if getattr(plugin_class, '_has_do_post_copy', False):
                # getattr is used for django CMS 3.4 compatibility
                # apps on 3.4 wishing to leverage this callback will need
                # to manually set the _has_do_post_copy attribute.
                plugin_class.do_post_copy(new_plugin, source_map)


class ArchivedPlugin(models.Model):
    data = JSONField(default={}, blank=True)
    placeholder = models.ForeignKey(
        ArchivedPlaceholder,
        on_delete=models.CASCADE,
        related_name='archived_plugins',
    )
    cms_plugin = models.OneToOneField(
        CMSPlugin,
        on_delete=models.CASCADE,
        related_name='trans_archived_plugin',
    )
    old_plugin_id = models.IntegerField()

    class Meta:
        default_permissions = ''
