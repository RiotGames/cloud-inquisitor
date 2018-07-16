from cloud_inquisitor.app import initialize
from cloud_inquisitor.plugins.commands import BaseCommand


class Setup(BaseCommand):
    """Sets up the initial state of the configuration stored in the database"""
    name = 'Setup'
    option_list = ()

    def run(self, **kwargs):
        initialize()
