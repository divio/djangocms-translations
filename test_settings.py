#!/usr/bin/env python
from __future__ import unicode_literals

HELPER_SETTINGS = {
    'TIME_ZONE': 'Europe/Zurich',
    'DATABASES': {
        'default': {
            # 'ENGINE': 'django.db.backends.postgresql',
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'djangocms_translation',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    },
}


def run():
    from djangocms_helper import runner
    runner.cms('djangocms_translations')

if __name__ == "__main__":
    run()
