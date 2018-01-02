from cms.test_utils.testcases import CMSTestCase

from djangocms_translations.providers.supertext import _get_content


class GetContentTestCase(CMSTestCase):
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
            '<p>Please <cms-plugin alt="Link/Button - click here " id="3" '
            'title="Link/Button - click here"></cms-plugin> to go to link1.</p>'
        )
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
            {
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
                'pk': 3
            }
        ]

        result = _get_content(raw_content, plugin, plugins)

        expected = (
            '<p>Please <cms-plugin alt="Link/Button - click here " id="3" '
            'title="Link/Button - click here">CLICK ON LINK1!!!</cms-plugin> to go to link1.</p>'
        )
        self.assertEquals(result, expected)

    def test_textfield_with_multiple_children(self):
        raw_content = (
            '<p>Please <cms-plugin alt="Link/Button - click here " id="3" '
            'title="Link/Button - click here"></cms-plugin> to go to link1 '
            'or <cms-plugin alt="Link/Button - click here " id="4" '
            'title="Link/Button - click here"></cms-plugin> to go to link2.</p>'
        )
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
            {
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
                'pk': 3
            },
            {
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
        ]

        result = _get_content(raw_content, plugin, plugins)

        expected = (
            '<p>Please <cms-plugin alt="Link/Button - click here " id="3" '
            'title="Link/Button - click here">CLICK ON LINK1!!!</cms-plugin> to go to link1 '
            'or <cms-plugin alt="Link/Button - click here " id="4" '
            'title="Link/Button - click here">CLICK ON LINK2!!!</cms-plugin> to go to link2.</p>'
        )
        self.assertEquals(result, expected)
