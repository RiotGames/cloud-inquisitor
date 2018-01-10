import os
import pkg_resources

from click import confirm
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from pkg_resources import iter_entry_points

from cloud_inquisitor import app, db, ServerWrapper
from cloud_inquisitor.log import setup_logging
from cloud_inquisitor.schema.resource import *

MIGRATIONS_PATH = os.path.join(pkg_resources.resource_filename('cloud_inquisitor', 'data'), 'migrations')

manager = Manager(app)
migrate = Migrate(app, db, directory=MIGRATIONS_PATH)

manager.add_command('db', MigrateCommand)
manager.add_command('runserver', ServerWrapper)


@manager.command
def drop_db():
    """ Drop the entire database, USE WITH CAUTION! """
    if confirm('Are you absolutely sure you want to drop the entire database? This cannot be undone!'):
        db.drop_all()


# Load custom commands
for ep in iter_entry_points('cloud_inquisitor.plugins.commands'):
    cls = ep.load()
    manager.add_command(ep.name, cls)

def cli():
    setup_logging()
    manager.run()
