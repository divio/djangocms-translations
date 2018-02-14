#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import os
import sys

import dj_database_url

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
    'DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER': os.environ.get('DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER'),
    'DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD': os.environ.get('DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD'),
    'DJANGOCMS_TRANSLATIONS_USE_STAGING': True,

    'DATABASES': {'default': dj_database_url.config(
        env='DJANGOCMS_TRANSLATIONS_DATABASE_URL',
        default='postgres://djangocmstranslations:djangocmstranslations@localhost:5432/djangocmstranslations'
    )},
    'INSTALLED_APPS': [
        'celery',
    ],
    'ALLOWED_HOSTS': [
        'localhost'
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
    'SITE_ID': 1,
    'DJANGOCMS_TRANSLATIONS_CONF': {
        'Bootstrap3ButtonCMSPlugin': {'text_field_child_label': 'label'},
        'DummyLinkPlugin': {'text_field_child_label': 'label'},
    },
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'CELERY_TASK_ALWAYS_EAGER': True,
}
if 'test' in sys.argv:
    HELPER_SETTINGS['MIGRATION_MODULES'] = DisableMigrations()
    HELPER_SETTINGS['INSTALLED_APPS'].append('tests')
    HELPER_SETTINGS['CMS_TEMPLATES'] = (
        ('test_fullwidth.html', 'Fullwidth'),
        ('test_page.html', 'Normal page'),
    )


def run():
    from djangocms_helper import runner
    runner.cms('djangocms_translations')


if __name__ == '__main__':
    run()
