from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import get_language_info, get_language_from_request, ugettext_lazy as _
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool


@toolbar_pool.register
class TranslationsToolbar(CMSToolbar):
    def populate(self):
        available_languages = settings.LANGUAGES
        if len(available_languages) < 2:
            return

        page = self.request.current_page
        if not page:
            return

        page_languages = page.get_languages()
        if len(page_languages) < 2:
            return

        menu = self.toolbar.get_or_create_menu('djangocms_translations', _('Translations'))
        overview_url = reverse('admin:djangocms_translations_translationrequest_changelist')
        menu.add_sideframe_item(_('Overview'), url=overview_url)

        current_language = get_language_from_request(self.request)
        base_querystring = 'cms_page={}&source_language={}'.format(page.id, current_language)
        base_url = '{}?{}'.format(reverse('admin:create-translation-request'), base_querystring)

        translate_menu = menu.get_or_create_menu(
            'djangocms_translations-translate',
            _('Translate this page'),
            position=1,
        )

        if not page.publisher_is_draft:
            page = page.publisher_draft

        for code in page.get_languages():
            if code != current_language:
                name = get_language_info(code)['name']
                sub_url = '{}&target_language={}'.format(base_url, code)
                translate_menu.add_modal_item(_('to {}'.format(name)), url=sub_url)
