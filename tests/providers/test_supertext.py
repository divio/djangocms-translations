import copy
import json

from cms.api import create_page, add_plugin
from cms.test_utils.testcases import CMSTestCase
from django.contrib.auth.models import User

from djangocms_transfer.exporter import export_page

from djangocms_translations.providers.supertext import (
    SupertextTranslationProvider, _get_translation_export_content, _set_translation_import_content,
)
from djangocms_translations.models import TranslationRequest, TranslationRequestItem, TranslationOrder


class GetTranslationExportContentTestCase(CMSTestCase):
    def setUp(self):
        super(GetTranslationExportContentTestCase, self).setUp()
        self.page = create_page('test page', 'test_page.html', 'en', published=True)
        self.placeholder = self.page.placeholders.get(slot='content')

    def _export_page(self):
        return json.loads(export_page(self.page, 'en'))

    def test_textfield_without_children(self):
        raw_content = '<p>Please <a href="http://www.google.com">CLICK ON LINK1</a> to go to link1.</p>'
        add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body=raw_content)

        plugin = self._export_page()[0]['plugins'][0]
        result, children_included_in_this_content = _get_translation_export_content('body', plugin)

        self.assertEquals(result, raw_content)
        self.assertEquals(children_included_in_this_content, [])

    def test_textfield_with_children(self):
        parent = add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1.</p>'
        ).format(child1.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result, children_included_in_this_content = _get_translation_export_content('body', plugin)

        expected = (
            parent_body
            .replace('></cms-plugin>', '>CLICK ON LINK1</cms-plugin>', 1)
        )
        self.assertEquals(result, expected)
        self.assertEquals(children_included_in_this_content, [child1.pk])

    def test_textfield_with_multiple_children(self):
        parent = add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        child2 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK2')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1 '
            'or <cms-plugin id="{}"></cms-plugin> to go to link2.</p>'
        ).format(child1.pk, child2.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result, children_included_in_this_content = _get_translation_export_content('body', plugin)

        expected = (
            parent_body
            .replace('></cms-plugin>', '>CLICK ON LINK1</cms-plugin>', 1)
            .replace('></cms-plugin>', '>CLICK ON LINK2</cms-plugin>', 1)
        )
        self.assertEquals(result, expected)
        self.assertEquals(children_included_in_this_content, [child1.pk, child2.pk])

    def test_textfield_with_multiple_children_one_deleted(self):
        parent = add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        child2 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK2')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1 '
            'or <cms-plugin id="{}"></cms-plugin> to go to link2.</p>'
        ).format(child1.pk, child2.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]

        child1.delete()

        result, children_included_in_this_content = _get_translation_export_content('body', plugin)

        expected = (
            '<p>Please  to go to link1 '
            'or <cms-plugin id="{}">CLICK ON LINK2</cms-plugin> to go to link2.</p>'
        ).format(child2.pk)
        self.assertEquals(result, expected)
        self.assertEquals(children_included_in_this_content, [child2.pk])

    def test_dummy_textfield2_with_children(self):
        ''' DummyText2Plugin implementation defines get_translation_export_content with a simple str return. '''
        parent = add_plugin(self.placeholder, 'DummyText2Plugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        parent_body = (
            '<p>Please <cms-pluginid="{}"></cms-plugin> to go to link1.</p>'
        ).format(child1.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result, children_included_in_this_content = _get_translation_export_content('body', plugin)

        self.assertEquals(result, 'super dummy overwritten content')
        self.assertEquals(children_included_in_this_content, [])

    def test_dummy_textfield3_with_children(self):
        ''' DummyText3Plugin implementation does not define get_translation_export_content. '''
        parent = add_plugin(self.placeholder, 'DummyText3Plugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1.</p>'
        ).format(child1.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result, children_included_in_this_content = _get_translation_export_content('body', plugin)

        self.assertEquals(result, parent.body)
        self.assertEquals(children_included_in_this_content, [])

    def test_textfield_with_children_non_translatable(self):
        parent = add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummySpacerPlugin', 'en', target=parent)
        parent_body = (
            '<p>This is cool <cms-plugin id="{}"></cms-plugin> this is nice.</p>'
        ).format(child1.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result, children_included_in_this_content = _get_translation_export_content('body', plugin)

        expected = (
            parent_body
        )
        self.assertEquals(result, expected)
        self.assertEquals(children_included_in_this_content, [child1.pk])


class SetTranslationImportContentTestCase(CMSTestCase):
    def setUp(self):
        super(SetTranslationImportContentTestCase, self).setUp()
        self.page = create_page('test page', 'test_page.html', 'en', published=True)
        self.placeholder = self.page.placeholders.get(slot='content')

    def _export_page(self):
        return json.loads(export_page(self.page, 'en'))

    def test_textfield_without_children(self):
        raw_content = '<p>Please <a href="http://www.google.com">CLICK ON LINK1</a> to go to link1.</p>'
        add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body=raw_content)

        plugin = self._export_page()[0]['plugins'][0]
        result = _set_translation_import_content(_get_translation_export_content('body', plugin)[0], plugin)

        self.assertDictEqual(result, {})

    def test_textfield_with_children(self):
        parent = add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1.</p>'
        ).format(child1.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result = _set_translation_import_content(_get_translation_export_content('body', plugin)[0], plugin)

        self.assertDictEqual(result, {child1.pk: 'CLICK ON LINK1'})

    def test_textfield_with_multiple_children(self):
        parent = add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        child2 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK2')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1 '
            'or <cms-plugin id="{}"></cms-plugin> to go to link2.</p>'
        ).format(child1.pk, child2.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result = _set_translation_import_content(_get_translation_export_content('body', plugin)[0], plugin)

        self.assertDictEqual(result, {child1.pk: 'CLICK ON LINK1', child2.pk: 'CLICK ON LINK2'})

    def test_textfield_with_multiple_children_one_deleted(self):
        parent = add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        child2 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK2')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1 '
            'or <cms-plugin id="{}"></cms-plugin> to go to link2.</p>'
        ).format(child1.pk, child2.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]

        child1.delete()

        result = _set_translation_import_content(_get_translation_export_content('body', plugin)[0], plugin)

        self.assertDictEqual(result, {child2.pk: 'CLICK ON LINK2'})

    def test_dummy_textfield2_with_children(self):
        ''' DummyText2Plugin implementation defines get_translation_export_content with a simple str return. '''
        parent = add_plugin(self.placeholder, 'DummyText2Plugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1.</p>'
        ).format(child1.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result = _set_translation_import_content(_get_translation_export_content('body', plugin)[0], plugin)

        self.assertDictEqual(result, {42: 'because I want this to be id=42'})

    def test_dummy_textfield3_with_children(self):
        ''' DummyText3Plugin implementation does not define get_translation_export_content. '''
        parent = add_plugin(self.placeholder, 'DummyText3Plugin', 'en', body='')
        child1 = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=parent, label='CLICK ON LINK1')
        parent_body = (
            '<p>Please <cms-plugin id="{}"></cms-plugin> to go to link1.</p>'
        ).format(child1.pk)
        parent.body = parent_body
        parent.save()

        plugin = self._export_page()[0]['plugins'][0]
        result = _set_translation_import_content(_get_translation_export_content('body', plugin)[0], plugin)

        self.assertDictEqual(result, {})


class SupertextTranslationProviderTestCase(CMSTestCase):
    def setUp(self):
        super(SupertextTranslationProviderTestCase, self).setUp()
        self.user = User.objects.create_superuser('djangocms', 'cms@example.com', '123456')
        self.page = create_page('test page', 'test_page.html', 'en', published=True)
        self.placeholder = self.page.placeholders.get(slot='content')

        self.parent = add_plugin(self.placeholder, 'DummyTextPlugin', 'en', body='')
        self.child = add_plugin(self.placeholder, 'DummyLinkPlugin', 'en', target=self.parent, label='contact me')
        self.child2 = add_plugin(self.placeholder, 'DummySpacerPlugin', 'en', target=self.parent)
        self.parent_body = (
            '<p>Please <cms-plugin id="{child_pk}"></cms-plugin> '
            '<cms-plugin id="{child2_pk}"></cms-plugin> one of these days.</p>'
        ).format(child_pk=self.child.pk, child2_pk=self.child2.pk)
        self.parent.body = self.parent_body
        self.parent.save()

        self.translation_request = TranslationRequest.objects.create(
            user=self.user,
            provider_backend='supertext',
            source_language='en',
            target_language='pt',
        )

        self.translation_request_item = TranslationRequestItem.objects.create(
            translation_request=self.translation_request,
            source_cms_page=self.page,
            target_cms_page=self.page,
        )

        self.translation_order = TranslationOrder.objects.create(request=self.translation_request)

        self.provider = SupertextTranslationProvider(self.translation_request)

        self.translation_request.export_content_from_cms()
        self.export_content = json.loads(self.translation_request.export_content)

        self.expected_request_content = {
            'Groups': [
                {
                    'Items': [
                        {
                            'Id': 'body',
                            'Content': _get_translation_export_content('body', self.export_content[0]['plugins'][0])[0],
                        },
                    ],
                    'GroupId': '{}:content:{}'.format(self.translation_request_item.pk, self.parent.id)
                },
            ],
            'ContentType': 'text/html',
            'SourceLang': 'en',
            'TargetLanguages': [
                'pt',
            ],
        }
        self.mock_response_content = copy.deepcopy(self.expected_request_content)
        self.mock_response_content['Groups'][0]['Items'][0]['Content'] = (
            self.mock_response_content['Groups'][0]['Items'][0]['Content']
            .replace('Please', 'Por favor')
            .replace('contact me', 'entre em contato comigo')
            .replace('one of these days', 'algum dia desses')
        )

    def test_get_export_data(self):
        export_data = self.provider.get_export_data()
        self.assertDictEqual(export_data, self.expected_request_content)

    def test_get_import_data(self):
        self.translation_request.request_content = self.expected_request_content
        self.translation_request.save()

        # request_content is not 100% the same between order and request, but this is ok for testing purposes.
        self.translation_order.request_content = self.translation_request.request_content
        self.translation_order.response_content = json.dumps(self.mock_response_content)
        self.translation_order.save()

        import_data = self.provider.get_import_data()

        self.assertIsInstance(import_data, dict)
        self.assertEquals(len(import_data), 1)
        self.assertTrue(self.translation_request_item.pk in import_data.keys())
        self.assertEquals(len(import_data[self.translation_request_item.pk]), 1)

        placeholder = import_data[self.translation_request_item.pk][0]
        self.assertEquals(len(placeholder.plugins), 3)
        self.assertEquals(placeholder.plugins[0].plugin_type, 'DummyTextPlugin')
        self.assertEquals(
            placeholder.plugins[0].data['body'],
            (
                '<p>Por favor <cms-plugin id="{}">entre em contato comigo</cms-plugin> '
                '<cms-plugin id="{}"></cms-plugin> algum dia desses.</p>'
            ).format(self.child.pk, self.child2.pk)
        )

        self.assertEquals(placeholder.plugins[1].plugin_type, 'DummyLinkPlugin')
        self.assertEquals(placeholder.plugins[1].data['label'], 'entre em contato comigo')

        self.assertEquals(placeholder.plugins[2].plugin_type, 'DummySpacerPlugin')
        self.assertEquals(placeholder.plugins[2].data, {})
