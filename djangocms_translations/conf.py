from django.conf import settings


TRANSLATIONS_CONF = getattr(settings, 'DJANGOCMS_TRANSLATIONS_CONF', {})
