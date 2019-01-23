# -*- coding: utf-8 -*-
import requests

from .. import conf


class ProviderException(Exception):
    pass


class BaseTranslationProvider(object):
    API_LIVE_URL = None
    API_STAGE_URL = None

    CURRENCY_KEY = None
    PRICE_KEY = None

    def __init__(self, request):
        self.request = request

    @property
    def api_url(self):
        if conf.TRANSLATIONS_USE_STAGING:
            return self.API_STAGE_URL
        return self.API_LIVE_URL

    def get_url(self, section):
        return '{}{}'.format(self.api_url, section)

    def get_headers(self):
        return NotImplementedError

    def make_request(self, method, section, **kwargs):
        return requests.request(
            method=method,
            url=self.get_url(section),
            headers=self.get_headers(),
            **kwargs
        )

    def get_export_data(self):
        raise NotImplementedError

    def get_import_data(self):
        raise NotImplementedError

    def get_quote(self):
        raise NotImplementedError

    def get_order_type_choices(self):
        raise NotImplementedError

    def get_delivery_time_choices(self):
        raise NotImplementedError

    def get_provider_options(self, **kwargs):
        raise NotImplementedError
