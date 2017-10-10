# -*- coding: utf-8 -*-
from aldryn_client import forms


class Form(forms.BaseForm):

    def to_settings(self, data, settings):
        if 'ALDRYN_SSO_LOGIN_WHITE_LIST' in settings:
            endpoint = '/admin/djangocms_translations/translationrequest/\w+/callback/'
            settings['ALDRYN_SSO_LOGIN_WHITE_LIST'].append(endpoint)
        return settings
