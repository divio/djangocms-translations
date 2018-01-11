import json
from collections import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse

import requests

from djangocms_transfer.forms import _object_version_data_hook
from djangocms_transfer.utils import get_plugin_class

from .. import __version__ as djangocms_translations_version
from ..utils import add_domain, get_translatable_fields, get_text_field_child_label

from .base import BaseTranslationProvider, ProviderException


def _get_content(field, raw_plugin):
    plugin_class = get_plugin_class(raw_plugin['plugin_type'])
    try:
        result = plugin_class.get_translation_content(field, raw_plugin['data'])
    except AttributeError:
        result = (raw_plugin['data'][field], [])
    return result


def _get_children_content(enriched_content, plugin):
    plugin_class = get_plugin_class(plugin['plugin_type'])
    try:
        result = plugin_class.get_translation_children_content(enriched_content, plugin['data'])
    except AttributeError:
        result = {}
    return result


class SupertextException(ProviderException):
    pass


class SupertextTranslationProvider(BaseTranslationProvider):
    API_LIVE_URL = 'https://www.supertext.ch/api/'
    API_STAGE_URL = 'https://dev.supertext.ch/api/'

    def get_headers(self):
        return {
            'Content-type': 'application/json; charset=UTF-8',
            'Accept': '*',
        }

    def get_auth(self):
        return (
            settings.DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER,
            settings.DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD,
        )

    def make_request(self, method, section, **kwargs):
        return requests.request(
            method=method,
            url=self.get_url(section),
            headers=self.get_headers(),
            auth=self.get_auth(),
            **kwargs
        )

    def get_export_data(self):
        data = {
            'ContentType': 'text/html',
            'SourceLang': self.request.source_language,
            'TargetLanguages': [self.request.target_language],
        }
        groups = []
        fields_by_plugin = {}

        for placeholder in json.loads(self.request.export_content):
            subplugins_already_processed = set()

            for raw_plugin in placeholder['plugins']:
                plugin_type = raw_plugin['plugin_type']

                if raw_plugin['pk'] in subplugins_already_processed:
                    continue

                if plugin_type not in fields_by_plugin:
                    fields_by_plugin[plugin_type] = get_translatable_fields(plugin_type)

                items = []
                for field in fields_by_plugin[plugin_type]:
                    content, children_included_in_this_content = _get_content(field, raw_plugin)
                    subplugins_already_processed.update(children_included_in_this_content)

                    if content:
                        items.append({
                            'Id': field,
                            'Content': content,
                        })

                if items:
                    groups.append({
                        'GroupId': '{}:{}'.format(placeholder['placeholder'], raw_plugin['pk']),
                        'Items': items
                    })

        data['Groups'] = groups
        return data

    def get_import_data(self):
        request = self.request
        export_content = json.loads(request.export_content)
        import_content = json.loads(request.order.response_content)
        subplugins_already_processed = set()

        # convert it to a format which is easier to work with
        export_content = {
            placeholder['placeholder']: OrderedDict(
                (plugin['pk'], plugin)
                for plugin in placeholder['plugins']
            )
            for placeholder in export_content
        }

        for group in import_content['Groups']:
            placeholder, plugin_id = group['GroupId'].rsplit(':', 1)
            plugin_id = int(plugin_id)

            if plugin_id in subplugins_already_processed:
                continue

            for item in group['Items']:
                plugin = export_content[placeholder][plugin_id]
                plugin['data'][item['Id']] = item['Content']
                subplugins = _get_children_content(item['Content'], plugin)
                subplugins_already_processed.update(list(subplugins.keys()))
                for subplugin_id, subplugin_content in subplugins.items():
                    field = get_text_field_child_label(export_content[placeholder][subplugin_id]['plugin_type'])
                    export_content[placeholder][subplugin_id]['data'][field] = subplugin_content

        # convert back into djangocms-transfer format
        data = json.dumps([{
            'placeholder': placeholder,
            'plugins': list(plugins.values()),
        } for placeholder, plugins in export_content.items()])
        return json.loads(data, object_hook=_object_version_data_hook)

    def get_quote(self):
        self.request.request_content = self.get_export_data()
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
        from djangocms_translations.models import TranslationOrder

        request = self.request

        callback_url = add_domain(reverse('admin:translation-request-provider-callback', kwargs={'pk': request.pk}))
        data = self.request.request_content
        data.update({
            'OrderName': 'djangocms-translations order #{}'.format(request.pk),
            'ReferenceData': request.pk,  # TODO: we should add a secret token here and then recheck when importing.
            'SystemName': request.source_cms_page.site.name,
            'ComponentName': 'djangocms-translations',
            'ComponentVersion': djangocms_translations_version,
            'CallbackUrl': callback_url,
        })

        data.update(request.selected_quote.provider_options)

        order = TranslationOrder.objects.create(
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
