from django.utils.safestring import mark_safe

from cms.plugin_rendering import _unpack_plugins, StructureRenderer
from cms.utils.plugins import build_plugin_tree

from djangocms_transfer.helpers import get_bound_plugins


class UnboundPluginRenderer(StructureRenderer):

    def __init__(self, *args, **kwargs):
        self._language = kwargs.pop('language')
        self._placeholders = kwargs.pop('placeholders')
        super(UnboundPluginRenderer, self).__init__(*args, **kwargs)

    def render(self):
        output = []

        for placeholder in self._placeholders:
            output.append(self.render_placeholder(placeholder, self._language))
        return mark_safe('\n'.join(output))

    def get_plugins_to_render(self, placeholder, *args, **kwargs):
        plugins = placeholder.get_plugins()

        if not plugins:
            return

        plugins = get_bound_plugins(plugins)
        # This sucks but the cms expects it when rendering
        # the structure of plugins.
        placeholder._plugins_cache = build_plugin_tree(plugins)

        for plugin in placeholder._plugins_cache:
            yield plugin

            if not plugin.child_plugin_instances:
                continue

            for plugin in _unpack_plugins(plugin):
                yield plugin

    def render_page_placeholder(self, page, placeholder, language=None):
        raise NotImplementedError

    def render_static_placeholder(self, static_placeholder, language=None):
        raise NotImplementedError
