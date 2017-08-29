import requests


class ProviderException(Exception):
    pass


class BaseTranslationProvider(object):
    BASE_API_URL = None

    def __init__(self, request):
        self.request = request

    def get_url(self, section):
        return '{}{}'.format(self.BASE_API_URL, section)

    def get_headers(self):
        return NotImplementedError

    def make_request(self, method, section, **kwargs):
        return requests.request(
            method=method,
            url=self.get_url(section),
            headers=self.get_headers(),
            **kwargs
        )

    def convert_for_export(self):
        raise NotImplementedError

    def convert_for_import(self, provider_response):
        raise NotImplementedError

    def get_quote(self):
        raise NotImplementedError
