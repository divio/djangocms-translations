# -*- coding: utf-8 -*-
from aldryn_client import forms


class Form(forms.BaseForm):

    def to_settings(self, data, settings):
        from functools import partial
        from aldryn_addons.utils import boolean_ish
        from aldryn_addons.utils import djsenv

        env = partial(djsenv, settings=settings)

        settings['DJANGOCMS_TRANSLATIONS_USE_STAGING'] = boolean_ish(env(
            'DJANGOCMS_TRANSLATIONS_USE_STAGING',
            default=True,
        ))

        if 'ALDRYN_SSO_LOGIN_WHITE_LIST' in settings:
            endpoint = '/admin/djangocms_translations/translationrequest/\w+/callback/'
            settings['ALDRYN_SSO_LOGIN_WHITE_LIST'].append(endpoint)
        return settings
