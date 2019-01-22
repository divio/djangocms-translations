# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cms.models import CMSPlugin
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class DummyText(CMSPlugin):
    body = models.TextField()

    class Meta:
        abstract = False

    def __str__(self):
        return 'dummy text object'


@python_2_unicode_compatible
class DummyLink(CMSPlugin):
    label = models.TextField()

    class Meta:
        abstract = False

    def __str__(self):
        return 'dummy link object'


@python_2_unicode_compatible
class DummySpacer(CMSPlugin):
    class Meta:
        abstract = False

    def __str__(self):
        return 'dummy spacer object'
