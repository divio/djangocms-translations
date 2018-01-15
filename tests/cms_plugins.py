import re

from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.utils.plugins import downcast_plugins

from tests.models import DummyText, DummyLink

from djangocms_translations.utils import get_text_field_child_label


@plugin_pool.register_plugin
class DummyTextPlugin(CMSPluginBase):
    render_plugin = False
    model = DummyText

    @staticmethod
    def get_translation_export_content(field, plugin_data):
        content = plugin_data[field]
        subplugins_within_this_content = []
        regex = re.compile(r'.*?<cms-plugin id="(?P<pk>\d+)"></cms-plugin>.*?')

        for subplugin in CMSPlugin.objects.filter(id__in=regex.findall(content)):
            subplugins_within_this_content.append(subplugin.id)
            subplugin = list(downcast_plugins([subplugin]))[0]
            subplugin_content = getattr(subplugin, get_text_field_child_label(subplugin.plugin_type))

            content = re.sub(
                r'<cms-plugin id="{}"></cms-plugin>'.format(subplugin.id),
                r'<cms-plugin id="{}">{}</cms-plugin>'.format(subplugin.id, subplugin_content),
                content
            )

        content = re.sub(r'<cms-plugin id="(\d+)"></cms-plugin>', '', content)
        return (content, subplugins_within_this_content)

    @staticmethod
    def set_translation_import_content(content, plugin):
        regex = re.compile(r'.*?<cms-plugin id="(?P<pk>\d+)">(?P<content>.*?)</cms-plugin>.*?')
        subplugin_data = regex.findall(content)

        return {
            int(subplugin_id): subplugin_content
            for subplugin_id, subplugin_content in subplugin_data
            if CMSPlugin.objects.filter(id=subplugin_id).exists()
        }


@plugin_pool.register_plugin
class DummyText2Plugin(CMSPluginBase):
    render_plugin = False
    model = DummyText

    @staticmethod
    def get_translation_export_content(field, plugin_data):
        return ('super dummy overwritten content', [])

    @staticmethod
    def set_translation_import_content(content, plugin):
        return {42: 'because I want this to be id=42'}


@plugin_pool.register_plugin
class DummyText3Plugin(CMSPluginBase):
    render_plugin = False
    model = DummyText


@plugin_pool.register_plugin
class DummyLinkPlugin(CMSPluginBase):
    render_plugin = False
    model = DummyLink
