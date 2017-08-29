import json

from django.conf import settings
from django.core.urlresolvers import reverse

import requests

from djangocms_transfer.forms import _object_version_data_hook

from .. import __version__ as djangocms_translations_version
from ..utils import add_domain
from .. import models

from .base import BaseTranslationProvider, ProviderException


class SupertextException(ProviderException):
    pass


class SupertextTranslationProvider(BaseTranslationProvider):
    # BASE_API_URL = 'https://www.supertext.ch/api/v1/'
    BASE_API_URL = 'https://dev.supertext.ch/api/'

    def get_headers(self):
        return {
            'Content-type': 'application/json; charset=UTF-8',
            'Accept': '*',
        }

    def get_auth(self):
        return settings.DJANGOCMS_TRANSLATIONS_SUPERTEXT_AUTH

    def make_request(self, method, section, **kwargs):
        return requests.request(
            method=method,
            url=self.get_url(section),
            headers=self.get_headers(),
            auth=self.get_auth(),
            **kwargs
        )

    def convert_for_export(self):
        data = {
            'ContentType': 'text/html',
            'Currency': 'chf',  # TODO
            'SourceLang': self.request.source_language,
            'TargetLanguages': [self.request.target_language],
        }

        groups = []

        for placeholder in json.loads(self.request.export_content):
            for plugin in placeholder['plugins']:
                items = [
                    {
                        'Context': key,
                        'Content': value,
                    }
                    for key, value in plugin['data'].items()
                    if value
                ]

                if items:
                    groups.append({
                        'GroupId': '{}:{}'.format(placeholder['placeholder'], plugin['pk']),
                        'Items': items
                    })

        data['Groups'] = groups
        return data

    def convert_for_import(self, provider_response):
        request = self.request

        export_content = json.loads(request.export_content)

        request.order.response_content = provider_response.body.decode('utf-8')
        request.order.save(update_fields=('response_content',))

        response_content = json.loads(request.order.response_content)

        # convert it to a format which is easier to work with
        export_content = {
            placeholder['placeholder']: {
                plugin['pk']: plugin
                for plugin in placeholder['plugins']
            }
            for placeholder in export_content
        }

        for group in response_content['Groups']:
            placeholder, plugin_id = group['GroupId'].rsplit(':', 1)
            plugin_id = int(plugin_id)

            for item in group['Items']:
                export_content[placeholder][plugin_id]['data'][item['Context']] = item['Content']

        # convert back into djangocms-transfer format
        data = json.dumps([{
            'placeholder': placeholder,
            'plugins': list(plugins.values()),
        } for placeholder, plugins in export_content.items()])

        return json.loads(
            data,
            object_hook=_object_version_data_hook,
        )

    def get_quote(self):
        self.request.request_content = self.convert_for_export()
        self.request.save(update_fields=('request_content',))
        response = self.make_request(
            method='post',
            section='v1/translation/quote',
            json=self.request.request_content,
        )
        if not response.ok:
            raise SupertextException(response.content)
        return response.json()

    def send_request(self):
        request = self.request

        data = self.request.request_content
        data.update({
            'OrderName': 'djangocms-translations order #{}'.format(request.pk),
            'ReferenceData': request.pk,  # TODO: we should add a secret token here and then recheck when importing the content
            'SystemName': request.cms_page.site.name,
            'ComponentName': 'djangocms-translations',
            'ComponentVersion': djangocms_translations_version,
            'CallbackUrl': add_domain(reverse('admin:translation-request-provider-callback', kwargs={'pk': request.pk})),
        })

        data.update(request.selected_quote.provider_options)

        order = models.TranslationOrder.objects.create(
            request=request,
            request_content=data,
        )

        response = self.make_request(
            method='post',
            section='v1/translation/order',
            json=order.request_content,
        )

        order.provider_details = response.json()
        order.save(update_fields=('provider_details',))
        if not response.ok:
            raise SupertextException(response.content)
        return response.json()

    def check_status(self):
        order = self.request.order
        response = self.make_request(
            method='get',
            section='v1/translation/order/{}'.format(order.provider_details['Id']),
            json=order.request_content,
        )

        if not response.ok:
            raise SupertextException(response.content)
        return response.json()
