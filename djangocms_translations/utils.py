import json

from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe

from cms.utils.i18n import get_language_objects

from yurl import URL

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter


def get_languages_for_current_site():
    return get_language_objects(Site.objects.get_current().pk)


def add_domain(url, domain=None):
    # add the domain to this url.
    if not domain:
        domain = Site.objects.get_current().domain
    url = URL(url)
    url = url.replace(scheme='http')  # TODO: https?
    url = url.replace(host=domain)
    return str(url)


def pretty_data(data, LexerClass):
    formatter = HtmlFormatter(style='colorful')
    data = highlight(data, LexerClass(), formatter)
    style = "<style>" + formatter.get_style_defs() + "</style><br>"
    return mark_safe(style + data)


def pretty_json(data):
    data = json.dumps(json.loads(data), sort_keys=True, indent=2)
    return pretty_data(data, JsonLexer)
