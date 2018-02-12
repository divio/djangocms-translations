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

        bulk_translate_url = reverse('admin:translate-in-bulk-step-1')
        menu.add_sideframe_item(_('Translate in bulk'), url=bulk_translate_url)

        current_language = get_language_from_request(self.request)
        base_url = (
            '{url}?source_cms_page={page_id}&target_cms_page={page_id}&source_language={source_language}'
            .format(url=reverse('admin:create-translation-request'), page_id=page.pk, source_language=current_language)
        )

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
