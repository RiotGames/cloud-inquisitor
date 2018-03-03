from collections import namedtuple

from flask_script import Option

from cloud_inquisitor import CINQ_PLUGINS
from cloud_inquisitor.constants import PLUGIN_NAMESPACES
from cloud_inquisitor.plugins.commands import BaseCommand

ListPluginType = namedtuple('ListPluginType', ('cls', 'module'))


class ListPlugins(BaseCommand):
    """List the plugins currently installed on the system"""
    ns = 'command_plugins'
    name = 'ListPlugins'
    option_list = [
        Option('--type', type=str, default=None, metavar='TYPE', help='Only show plugins of this type',
               choices=list(PLUGIN_NAMESPACES.keys())
               )
    ]

    def run(self, **kwargs):
        self.log.info('--- List of Plugins ---')
        for ns, info in CINQ_PLUGINS.items():
            self.log.info('  {} Plugins:'.format(info['name'].capitalize()))
            for ep in info['plugins']:
                self.log.info('    {} from {}'.format(ep.attrs[0], ep.module_name))
            self.log.info('')
        self.log.info('--- End list of Plugins ---')
