# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from django.conf import settings

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

app = Celery('djangocms_translations')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
