from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import (
    get_language_info,
    get_language_from_request,
    ugettext_lazy as _,
)

from cms.toolbar_pool import toolbar_pool
from cms.toolbar_base import CMSToolbar


@toolbar_pool.register
class TranslationsToolbar(CMSToolbar):
    def populate(self):
        available_languages = settings.LANGUAGES
        if len(available_languages) > 1:
            is_multilingual = True
        else:
            is_multilingual = False

        if not is_multilingual:
            return

        page = self.request.current_page
        if not page:
            return

        menu = self.toolbar.get_or_create_menu(
            'djangocms_translations',
            _('Translations'),
        )
        url = reverse('admin:djangocms_translations_translationrequest_changelist')

        menu.add_sideframe_item(_('Overview'), url=url)

        current_language = get_language_from_request(self.request)

        translate_menu = menu.get_or_create_menu(
            'djangocms_translations-translate',
            _('Translate this page'),
            position=1,
        )

        if not page.publisher_is_draft:
            page = page.publisher_draft

        url = '{}?cms_page_id={}&source_lang={}'.format(
            reverse('admin:create-translation-request'),
            page.id,
            current_language,
        )

        for code in page.get_languages():
            if code != current_language:
                name = get_language_info(code)['name']
                translate_menu.add_modal_item(
                    _('to {}'.format(name)),
                    url='{}&target_lang={}'.format(url, code),
                )
