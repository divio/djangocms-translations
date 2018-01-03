from cms.models import Placeholder
from cms.test_utils.testcases import CMSTestCase
from djangocms_translations.providers.supertext import _get_content
from djangocms_transfer.datastructures import ArchivedPlugin


class GetContentTestCase(CMSTestCase):
    def setUp(self):
        super(GetContentTestCase, self).setUp()
        self.placeholder = Placeholder.objects.create(slot='test')
        self.child1_data = {
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'label': 'CLICK ON LINK1!!!',
            },
            'parent_id': None,
            'pk': None,
            'plugin_type': 'DummyLinkPlugin',
            'position': 0,
        }
        self.child2_data = {
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'label': 'CLICK ON LINK2!!!',
            },
            'parent_id': None,
            'pk': None,
            'plugin_type': 'DummyLinkPlugin',
            'position': 0,
        }

    def test_textfield_without_children(self):
        raw_content = '<p>Please <a href="http://www.google.com">CLICK ON LINK1!!!</a> to go to link1.</p>'
        plugin = {
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'body': raw_content
            },
            'parent_id': None,
            'pk': None,
            'plugin_type': 'DummyTextPlugin',
            'position': 1,
        }

        ArchivedPlugin(**plugin).restore(self.placeholder, 'en')

        result = _get_content('body', plugin)

        self.assertEquals(result, raw_content)

    def test_textfield_with_children(self):
        raw_content = (
            '<p>Please <cms-plugin alt="Dummy Link Plugin - dummy link object " '
            'title="Dummy Link Plugin - dummy link object" id="CHILD1ID"></cms-plugin> to go to link1.</p>'
        )
        plugin = {
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'body': raw_content
            },
            'parent_id': None,
            'pk': None,
            'plugin_type': 'DummyTextPlugin',
            'position': 1,
        }

        parent = ArchivedPlugin(**plugin).restore(self.placeholder, 'en')
        child1 = ArchivedPlugin(**self.child1_data).restore(self.placeholder, 'en', parent=parent)
        raw_content = raw_content.replace('CHILD1ID', str(child1.pk))
        plugin['data']['body'] = raw_content
        parent.body = raw_content
        parent.save()

        result = _get_content('body', plugin)

        expected = (
            '<p>Please <cms-plugin alt="Dummy Link Plugin - dummy link object "'
            'title="Dummy Link Plugin - dummy link object" id="{}">CLICK ON LINK1!!!</cms-plugin> to go to link1.</p>'
        ).format(child1.pk)
        self.assertEquals(result, expected)

    def test_textfield_with_multiple_children(self):
        raw_content = (
            '<p>Please <cms-plugin alt="Dummy Link Plugin - dummy link object " '
            'title="Dummy Link Plugin - dummy link object" id="CHILD1ID"></cms-plugin> to go to link1 '
            'or <cms-plugin alt="Dummy Link Plugin - dummy link object " '
            'title="Dummy Link Plugin - dummy link object" id="CHILD2ID"></cms-plugin> to go to link2.</p>'
        )
        plugin = {
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'body': raw_content
            },
            'parent_id': None,
            'pk': None,
            'plugin_type': 'DummyTextPlugin',
            'position': 1,
        }

        parent = ArchivedPlugin(**plugin).restore(self.placeholder, 'en')
        child1 = ArchivedPlugin(**self.child1_data).restore(self.placeholder, 'en', parent=parent)
        child2 = ArchivedPlugin(**self.child2_data).restore(self.placeholder, 'en', parent=parent)
        raw_content = raw_content.replace('CHILD1ID', str(child1.pk))
        raw_content = raw_content.replace('CHILD2ID', str(child2.pk))
        plugin['data']['body'] = raw_content
        parent.body = raw_content
        parent.save()

        result = _get_content('body', plugin)

        expected = (
            '<p>Please <cms-plugin alt="Dummy Link Plugin - dummy link object "'
            'title="Dummy Link Plugin - dummy link object" id="{}">CLICK ON LINK1!!!</cms-plugin> to go to link1 '
            'or <cms-plugin alt="Dummy Link Plugin - dummy link object "'
            'title="Dummy Link Plugin - dummy link object" id="{}">CLICK ON LINK2!!!</cms-plugin> to go to link2.</p>'
        ).format(child1.pk, child2.pk)
        self.assertEquals(result, expected)

    def test_textfield_with_multiple_children_one_deleted(self):
        raw_content = (
            '<p>Please <cms-plugin alt="Dummy Link Plugin - dummy link object " '
            'title="Dummy Link Plugin - dummy link object" id="CHILD1ID"></cms-plugin> to go to link1 '
            'or <cms-plugin alt="Dummy Link Plugin - dummy link object " '
            'title="Dummy Link Plugin - dummy link object" id="CHILD2ID"></cms-plugin> to go to link2.</p>'
        )
        plugin = {
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'body': raw_content
            },
            'parent_id': None,
            'pk': None,
            'plugin_type': 'DummyTextPlugin',
            'position': 1,
        }

        parent = ArchivedPlugin(**plugin).restore(self.placeholder, 'en')
        child1 = ArchivedPlugin(**self.child1_data).restore(self.placeholder, 'en', parent=parent)
        child2 = ArchivedPlugin(**self.child2_data).restore(self.placeholder, 'en', parent=parent)
        raw_content = raw_content.replace('CHILD1ID', str(child1.pk))
        raw_content = raw_content.replace('CHILD2ID', str(child2.pk))
        plugin['data']['body'] = raw_content
        parent.body = raw_content
        parent.save()

        child1.delete()

        result = _get_content('body', plugin)

        expected = (
            '<p>Please  to go to link1 '
            'or <cms-plugin alt="Dummy Link Plugin - dummy link object "'
            'title="Dummy Link Plugin - dummy link object" id="{}">CLICK ON LINK2!!!</cms-plugin> to go to link2.</p>'
        ).format(child2.pk)
        self.assertEquals(result, expected)

    def test_dummy_textfield2_with_children(self):
        ''' DummyText2Plugin implementation defines get_translation_content with a simple str return. '''
        raw_content = (
            '<p>Please <cms-plugin alt="Dummy Link Plugin - dummy link object " '
            'title="Dummy Link Plugin - dummy link object" id="CHILD1ID"></cms-plugin> to go to link1.</p>'
        )
        plugin = {
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'body': raw_content
            },
            'parent_id': None,
            'pk': None,
            'plugin_type': 'DummyText2Plugin',
            'position': 1,
        }

        parent = ArchivedPlugin(**plugin).restore(self.placeholder, 'en')
        child1 = ArchivedPlugin(**self.child1_data).restore(self.placeholder, 'en', parent=parent)
        raw_content = raw_content.replace('CHILD1ID', str(child1.pk))
        plugin['data']['body'] = raw_content
        parent.body = raw_content
        parent.save()

        result = _get_content('body', plugin)

        self.assertEquals(result, 'super dummy overwritten content')

    def test_dummy_textfield3_with_children(self):
        ''' DummyText3Plugin implementation does not define get_translation_content. '''
        raw_content = (
            '<p>Please <cms-plugin alt="Dummy Link Plugin - dummy link object " '
            'title="Dummy Link Plugin - dummy link object" id="CHILD1ID"></cms-plugin> to go to link1.</p>'
        )
        plugin = {
            'creation_date': '2018-01-02T12:12:12.000Z',
            'data': {
                'body': raw_content
            },
            'parent_id': None,
            'pk': None,
            'plugin_type': 'DummyText3Plugin',
            'position': 1,
        }

        parent = ArchivedPlugin(**plugin).restore(self.placeholder, 'en')
        child1 = ArchivedPlugin(**self.child1_data).restore(self.placeholder, 'en', parent=parent)
        raw_content = raw_content.replace('CHILD1ID', str(child1.pk))
        plugin['data']['body'] = raw_content
        parent.body = raw_content
        parent.save()

        result = _get_content('body', plugin)

        self.assertEquals(result, raw_content)
