import json
from itertools import chain
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import BooleanField
from django.forms import modelform_factory
from django.utils.lru_cache import lru_cache
from django.utils.safestring import mark_safe
from django.utils.translation import get_language_info

from yurl import URL

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from djangocms_transfer.utils import get_plugin_class, get_plugin_model

from .conf import TRANSLATIONS_CONF


USE_HTTPS = getattr(settings, 'URLS_USE_HTTPS', False)


def get_plugin_form_class(plugin_type, fields):
    plugin_class = get_plugin_class(plugin_type)
    plugin_fields = chain(
        plugin_class.model._meta.concrete_fields,
        plugin_class.model._meta.private_fields,
        plugin_class.model._meta.many_to_many,
    )
    plugin_fields_disabled = [
        field.name for field in plugin_fields
        if not getattr(field, 'editable', False)
    ]
    plugin_form_class = modelform_factory(
        plugin_class.model,
        fields=fields,
        exclude=plugin_fields_disabled,
    )
    return plugin_form_class


def get_plugin_form(plugin_type, data):
    _data = data.copy()
    plugin_form_class = get_plugin_form_class(plugin_type, fields=data.keys())
    multi_value_fields = [
        (name, field) for name, field in plugin_form_class.base_fields.items()
        if hasattr(field.widget, 'decompress') and name in data
    ]

    for name, field in multi_value_fields:
        # The value used on the form data is compressed,
        # and the form contains multi-value fields which expect
        # a decompressed value.
        compressed = data[name]

        try:
            decompressed = field.widget.decompress(compressed)
        except ObjectDoesNotExist:
            break

        for pos, value in enumerate(decompressed):
            _data['{}_{}'.format(name, pos)] = value
    return plugin_form_class(_data)


def add_domain(url, domain=None):
    # add the domain to this url.
    if domain is None:
        domain = Site.objects.get_current().domain

    url = URL(url)

    if USE_HTTPS:
        url = url.replace(scheme='https')
    else:
        url = url.replace(scheme='http')
    return str(url.replace(host=domain))


def pretty_data(data, LexerClass):
    formatter = HtmlFormatter(style='colorful')
    data = highlight(data, LexerClass(), formatter)
    style = "<style>" + formatter.get_style_defs() + "</style><br>"
    return mark_safe(style + data)


def pretty_json(data):
    data = json.dumps(json.loads(data), sort_keys=True, indent=2)
    return pretty_data(data, JsonLexer)


@lru_cache(maxsize=None)
def get_translatable_fields(plugin_type):
    conf = TRANSLATIONS_CONF.get(plugin_type, {})

    if 'fields' in conf:
        fields = conf['fields']
    else:
        model = get_plugin_model(plugin_type)

        opts = model._meta.concrete_model._meta
        fields = opts.local_fields
        fields = [
            field.name
            for field in fields
            if (
                not field.is_relation
                and not field.primary_key
                and not field.choices
                and not isinstance(field, BooleanField)
            )
        ]

    excluded = conf.get('excluded_fields', [])
    return set(fields).difference(set(excluded))


@lru_cache(maxsize=None)
def get_text_field_child_label(plugin_type):
    return settings.DJANGOCMS_TRANSLATIONS_CONF.get(plugin_type, {}).get('text_field_child_label')


def get_language_name(lang_code):
    info = get_language_info(lang_code)
    if info['code'] == lang_code:
        return info['name']
    try:
        return dict(settings.LANGUAGES)[lang_code]
    except KeyError:
        # fallback to known name
        return info['name']


def get_page_url(page, language, is_https=False):
    return urljoin(
        'http{}://{}'.format(
            's' if is_https else '',
            page.node.site.domain,
        ),
        page.get_absolute_url(language=language),
    )
