import re

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.conf import settings

from djangocms_text_ckeditor.utils import (
    OBJ_ADMIN_RE_PATTERN, plugin_to_tag, _plugin_tags_to_html, plugin_tags_to_id_list,
)

from tests.models import DummyText, DummyLink


@plugin_pool.register_plugin
class DummyTextPlugin(CMSPluginBase):
    render_plugin = False
    model = DummyText

    @staticmethod
    def get_translation_content(field, plugin_data):
        def _render_plugin_with_content(obj, match):
            field = settings.DJANGOCMS_TRANSLATIONS_CONF[obj.plugin_type]['text_field_child_label']
            content = getattr(obj, field)
            return plugin_to_tag(obj, content)

        content = _plugin_tags_to_html(plugin_data[field], output_func=_render_plugin_with_content)
        subplugins_within_this_content = plugin_tags_to_id_list(content)
        return content, subplugins_within_this_content

    @staticmethod
    def get_translation_children_content(content, plugin):
        def _rreplace(text, old, new, count):
            return new.join(text.rsplit(old, count))

        OBJ_ADMIN_RE_PATTERN_WITH_CONTENT = _rreplace(OBJ_ADMIN_RE_PATTERN, '.*?', '(?P<content>.*?)', 1)
        data = [x.groups() for x in re.finditer(OBJ_ADMIN_RE_PATTERN_WITH_CONTENT, content)]
        data = {int(k): v for k, v in data}

        return {
            subplugin_id: data[subplugin_id]
            for subplugin_id in plugin_tags_to_id_list(content)
        }


@plugin_pool.register_plugin
class DummyText2Plugin(CMSPluginBase):
    render_plugin = False
    model = DummyText

    @staticmethod
    def get_translation_content(field, plugin_data):
        return 'super dummy overwritten content', []

    @staticmethod
    def get_translation_children_content(content, plugin):
        return {42: 'because I want this to be id=42'}


@plugin_pool.register_plugin
class DummyText3Plugin(CMSPluginBase):
    render_plugin = False
    model = DummyText


@plugin_pool.register_plugin
class DummyLinkPlugin(CMSPluginBase):
    render_plugin = False
    model = DummyLink
