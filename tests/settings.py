#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import os
import sys
import django
from tests.celery import app  # noqa


class DisableMigrations(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        from distutils.version import LooseVersion
        import django
        DJANGO_1_9 = LooseVersion(django.get_version()) < LooseVersion('1.10')
        if DJANGO_1_9:
            return 'notmigrations'
        else:
            return None


HELPER_SETTINGS = {
    'INSTALLED_APPS': [
        'celery',
    ],
    'CMS_LANGUAGES': {
        1: [
            {
                'code': 'en',
                'name': 'English',
            },
            {
                'code': 'pt-br',
                'name': 'Brazilian Portugues',
            },
            {
                'code': 'de',
                'name': 'Deutsch',
            },
        ],
    },
    'LANGUAGE_CODE': 'en',
    'LANGUAGES': [
        ('en', 'English'),
        ('pt-br', 'Brazilian Portugues'),
        ('de', 'Deutsch'),
    ],
    'ALLOWED_HOSTS': ['localhost'],
    'SITE_ID': 1,
    'DJANGOCMS_TRANSLATIONS_CONF': {
        'Bootstrap3ButtonCMSPlugin': {'text_field_child_label': 'label'},
        'DummyLinkPlugin': {'text_field_child_label': 'label'},
    },
    'CELERY_EAGER_PROPAGATES_EXCEPTIONS': True,
    'CELERY_ALWAYS_EAGER': True,
    'DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER': os.environ.get('DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER'),
    'DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD': os.environ.get('DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD'),
    'DJANGOCMS_TRANSLATIONS_USE_STAGING': True,
}


if 'test' in sys.argv:
    HELPER_SETTINGS['MIGRATION_MODULES'] = DisableMigrations()
    HELPER_SETTINGS['INSTALLED_APPS'].append('tests')
    HELPER_SETTINGS['CMS_TEMPLATES'] = (
        ('test_fullwidth.html', 'Fullwidth'),
        ('test_page.html', 'Normal page'),
    )

if __name__ == '__main__':
    from django.test.utils import get_runner
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
    django.setup()
    TestRunner = get_runner(settings=None)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests'])
    sys.exit(bool(failures))
