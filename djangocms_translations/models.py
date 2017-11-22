from __future__ import unicode_literals

import json

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db import IntegrityError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cms.models.fields import PageField

from extended_choices import Choices
from djangocms_transfer.exporter import get_page_export_data
from djangocms_transfer.importer import import_plugins_to_page

from .providers import SupertextTranslationProvider, TRANSLATION_PROVIDERS


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

    cms_page = PageField()

    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
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
        if not self.cms_page and not self.source_language:
            raise RuntimeError('Set a cms page and language for export')

        export_data = get_page_export_data(self.cms_page, self.source_language)
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
            content = self.provider.get_import_data()
        except ValueError:
            return self.set_status(self.STATES.IMPORT_FAILED)

        try:
            import_plugins_to_page(
                placeholders=content,
                page=self.cms_page,
                language=self.target_language
            )
        except IntegrityError:
            return self.set_status(self.STATES.IMPORT_FAILED)

        self.set_status(self.STATES.IMPORTED, commit=False)
        self.date_imported = timezone.now()
        self.save(update_fields=('date_imported', 'state'))
        return True


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
