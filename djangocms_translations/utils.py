import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.lru_cache import lru_cache
from django.utils.safestring import mark_safe

from cms.utils.i18n import get_language_objects

from yurl import URL

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from djangocms_transfer.utils import get_local_fields, get_plugin_model

from .conf import TRANSLATIONS_CONF


USE_HTTPS = getattr(settings, 'URLS_USE_HTTPS', False)


def get_languages_for_current_site():
    return get_language_objects(Site.objects.get_current().pk)


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
        fields = get_local_fields(model)
    excluded = conf.get('excluded_fields', [])
    return set(fields).difference(set(excluded))
