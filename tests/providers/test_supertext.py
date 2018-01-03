from cms.api import add_plugin
from cms.models import Placeholder
from cms.test_utils.testcases import CMSTestCase

from djangocms_translations.providers.supertext import _get_content


class GetContentTestCase(CMSTestCase):
    def setUp(self):
        super(GetContentTestCase, self).setUp()
        self.placeholder = Placeholder.objects.create(slot='test')

        self.child1_data = {
            'parent_id': 2,
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'classes': '',
                'link_url': 'http://www.google.com',
                'link_target': '',
                'link_page': None,
                'link_mailto': '',
                'link_attributes': {},
                'link_file': None,
                'btn_block': False,
                'link_phone': '',
                'btn_size': 'md',
                'type': 'lnk',
                'btn_context': 'default',
                'link_anchor': '',
                'icon_right': '',
                'icon_left': '',
                'label': 'CLICK ON LINK1!!!',
                'txt_context': ''
            },
            'position': 0,
            'plugin_type': 'Bootstrap3ButtonCMSPlugin',
            'pk': None
        }
        self.child1 = add_plugin(self.placeholder, 'Bootstrap3ButtonCMSPlugin', 'en', **self.child1_data['data'])
        self.child1_data['pk'] = self.child1.pk

        self.child2_data = {
            'parent_id': 2,
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'classes': '',
                'link_url': 'http://www.google.com',
                'link_target': '',
                'link_page': None,
                'link_mailto': '',
                'link_attributes': {},
                'link_file': None,
                'btn_block': False,
                'link_phone': '',
                'btn_size': 'md',
                'type': 'lnk',
                'btn_context': 'default',
                'link_anchor': '',
                'icon_right': '',
                'icon_left': '',
                'label': 'CLICK ON LINK2!!!',
                'txt_context': ''
            },
            'position': 0,
            'plugin_type': 'Bootstrap3ButtonCMSPlugin',
            'pk': 4
        }
        self.child2 = add_plugin(self.placeholder, 'Bootstrap3ButtonCMSPlugin', 'en', **self.child2_data['data'])
        self.child2_data['pk'] = self.child2.pk

    def test_textfield_without_children(self):
        raw_content = '<p>Please <a href="http://www.google.com">CLICK ON LINK1!!!</a> to go to link1.</p>'
        plugin = {
            'parent_id': None,
            'position': 1,
            'pk': 2,
            'creation_date': '2018-01-02T12:12:12.000Z',
            'plugin_type': 'TextPlugin',
            'data': {
                'body': raw_content
            }
        }
        plugins = [
            plugin,
        ]

        result = _get_content(raw_content, plugin, plugins)

        self.assertEquals(result, raw_content)

    def test_textfield_with_children(self):
        raw_content = (
            '<p>Please <cms-plugin alt="Link/Button - CLICK ON LINK1!!! " '
            'title="Link/Button - CLICK ON LINK1!!!" id="{}"></cms-plugin> to go to link1.</p>'
        ).format(self.child1.pk)
        plugin = {
            'parent_id': None,
            'position': 1,
            'pk': 2,
            'creation_date': '2018-01-02T12:12:12.000Z',
            'plugin_type': 'TextPlugin',
            'data': {
                'body': raw_content
            }
        }
        plugins = [
            plugin,
            self.child1_data,
        ]

        result = _get_content(raw_content, plugin, plugins)

        expected = (
            '<p>Please <cms-plugin alt="Link/Button - CLICK ON LINK1!!! "'
            'title="Link/Button - CLICK ON LINK1!!!" id="{}">CLICK ON LINK1!!!</cms-plugin> to go to link1.</p>'
        ).format(self.child1.pk)
        self.assertEquals(result, expected)

    def test_textfield_with_multiple_children(self):
        raw_content = (
            '<p>Please <cms-plugin alt="Link/Button - CLICK ON LINK1!!! " '
            'title="Link/Button - CLICK ON LINK1!!!" id="{}"></cms-plugin> to go to link1 '
            'or <cms-plugin alt="Link/Button - CLICK ON LINK2!!! " '
            'title="Link/Button - CLICK ON LINK2!!!" id="{}"></cms-plugin> to go to link2.</p>'
        ).format(self.child1.pk, self.child2.pk)
        plugin = {
            'parent_id': None,
            'position': 1,
            'pk': 2,
            'creation_date': '2018-01-02T12:12:12.000Z',
            'plugin_type': 'TextPlugin',
            'data': {
                'body': raw_content
            }
        }
        plugins = [
            plugin,
            self.child1_data,
            self.child2_data,
        ]

        result = _get_content(raw_content, plugin, plugins)

        expected = (
            '<p>Please <cms-plugin alt="Link/Button - CLICK ON LINK1!!! "'
            'title="Link/Button - CLICK ON LINK1!!!" id="{}">CLICK ON LINK1!!!</cms-plugin> to go to link1 '
            'or <cms-plugin alt="Link/Button - CLICK ON LINK2!!! "'
            'title="Link/Button - CLICK ON LINK2!!!" id="{}">CLICK ON LINK2!!!</cms-plugin> to go to link2.</p>'
        ).format(self.child1.pk, self.child2.pk)
        self.assertEquals(result, expected)

    def test_textfield_with_children_deleted(self):
        self.child1.delete()

        raw_content = (
            '<p>Please <cms-plugin alt="Link/Button - CLICK ON LINK1!!! " '
            'title="Link/Button - CLICK ON LINK1!!!" id="{}"></cms-plugin> to go to link1.</p>'
        ).format(self.child1.pk)
        plugin = {
            'parent_id': None,
            'position': 1,
            'pk': 2,
            'creation_date': '2018-01-02T12:12:12.000Z',
            'plugin_type': 'TextPlugin',
            'data': {
                'body': raw_content
            }
        }
        plugins = [
            plugin,
            self.child1_data,
        ]

        result = _get_content(raw_content, plugin, plugins)

        expected = '<p>Please  to go to link1.</p>'
        self.assertEquals(result, expected)
