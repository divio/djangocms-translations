# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DjangocmsTranslationsConfig(AppConfig):
    name = 'djangocms_translations'
    verbose_name = _('django CMS Translations')
