from collections import defaultdict, namedtuple

from flask_script import Option
from pkg_resources import iter_entry_points

from cloud_inquisitor.constants import PLUGIN_NAMESPACES
from cloud_inquisitor.plugins.commands import BaseCommand

ListPluginType = namedtuple('ListPluginType', ('cls', 'module'))

class ListPlugins(BaseCommand):
    """List the plugins currently installed on the system"""
    ns = 'command_plugins'
    name = 'ListPlugins'
    option_list = [
        Option('--type', type=str, default=None, metavar='TYPE', help='Only show plugins of this type',
               choices=list(PLUGIN_NAMESPACES.keys()))
    ]

    def run(self, **kwargs):
        plugins = defaultdict(list)

        if kwargs['type']:
            plugin_type = kwargs['type'].lower()
            for ns in PLUGIN_NAMESPACES[plugin_type]:
                for ep in iter_entry_points(ns):
                    plugins[plugin_type].append(ListPluginType(ep.attrs[0], ep.module_name))
        else:
            # List all plugins
            for plugin_type, namespaces in PLUGIN_NAMESPACES.items():
                for ns in namespaces:
                    for ep in iter_entry_points(ns):
                        plugins[plugin_type].append(ListPluginType(ep.attrs[0], ep.module_name))

        self.log.info('--- List of Plugins ---')
        for plugin_type, plugins in plugins.items():
            self.log.info('  {} Plugins:'.format(plugin_type.capitalize()))
            for plugin in plugins:
                self.log.info('    {} from {}'.format(plugin.cls, plugin.module))
            self.log.info('')
        self.log.info('--- End list of Plugins ---')
