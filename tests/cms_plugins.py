from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from tests.models import DummyText, DummyLink


@plugin_pool.register_plugin
class DummyTextPlugin(CMSPluginBase):
    render_plugin = False
    model = DummyText

    @staticmethod
    def get_djangocms_translation_content(instance):
        from djangocms_text_ckeditor.utils import plugin_to_tag, _plugin_tags_to_html

        def _render_plugin_with_content(obj, match):
            content = obj.label
            return plugin_to_tag(obj, content)

        return _plugin_tags_to_html(instance.body, output_func=_render_plugin_with_content)


@plugin_pool.register_plugin
class DummyText2Plugin(CMSPluginBase):
    render_plugin = False
    model = DummyText

    @staticmethod
    def get_djangocms_translation_content(instance):
        return 'super dummy overwritten content'


@plugin_pool.register_plugin
class DummyText3Plugin(CMSPluginBase):
    render_plugin = False
    model = DummyText


@plugin_pool.register_plugin
class DummyLinkPlugin(CMSPluginBase):
    render_plugin = False
    model = DummyLink
