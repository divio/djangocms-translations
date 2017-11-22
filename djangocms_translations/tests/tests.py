# -*- coding: utf-8 -*-
import json

from django.contrib.auth.models import User
from django.test import TestCase

from cms.test_utils.testcases import BaseCMSTestCase

from ..models import TranslationRequest


class SupertextTranslationProviderTestCase(TestCase, BaseCMSTestCase):

    def setUp(self):
        with open('fixture.json', 'r') as fh:
            content = json.load(fh)

        self.request = TranslationRequest.objects.create(
            user=User.objects.get_or_create(username='root')[0],
            provider_backend=TranslationRequest.PROVIDERS.SUPERTEXT,
            request_content=content,
        )

    def tearDown(self):
        self.request.delete()

    def test_import_export(self):
        request = self.request
        provider = request.provider

        before = request.request_content
        export_data = provider.get_export_data()
        request.response_content = export_data
        after = provider.get_import_data()

        self.assertEqual(before, after)
