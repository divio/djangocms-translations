#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import os

import dj_database_url

HELPER_SETTINGS = {
    'DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER': os.environ.get('DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER'),
    'DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD': os.environ.get('DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD'),
    'DJANGOCMS_TRANSLATIONS_USE_STAGING': True,

    'DATABASES': {'default': dj_database_url.config(
        env='DJANGOCMS_TRANSLATIONS_DATABASE_URL',
        default='postgres://djangocmstranslations:djangocmstranslations@localhost:5432/djangocmstranslations'
    )},

    'INSTALLED_APPS': [
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
        ],
    },
    'LANGUAGE_CODE': 'en',
    'LANGUAGES': [
        ('en', 'English'),
        ('pt-br', 'Brazilian Portugues'),
    ],
    'SITE_ID': 1,
}


def run():
    from djangocms_helper import runner
    runner.cms('djangocms_translations')


if __name__ == '__main__':
    run()
