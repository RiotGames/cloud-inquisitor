import os
import subprocess
from sys import modules, exit
if 'flask.app' in modules:
    print('Flask Module Already Imported! Exiting to prevent destruction of possibly existing data')
    exit(-1)

from flask_script import Manager

os.environ['CINQ_SETTINGS'] = '../settings/testconfig.py'
from cloud_inquisitor import app, db, register_views
from cloud_inquisitor.plugins.commands import setup

import pytest


@pytest.fixture(scope='session', autouse=True)
def prepare_app():
    create_db_and_user()
    # python3 manage.py db upgrade
    db.drop_all()
    db.create_all()

    # python3 manage.py setup
    manager = Manager(app)
    manager.add_command('setup', setup.Setup)
    manager.handle('manage.py', ['setup', '--headless'])

    app.reload_dbconfig()
    register_views()

    yield  # Wait until tests are done
    cleanup()


def create_db_and_user():
    """Database contains JSON datatype, which requires Postgres DB available"""
    # sudo mysql -u root -e "create database cloud_inquisitor; grant ALL on cloud_inquisitor.* to 'cloud_inquisitor'@'localhost' identified by 'changeme';" || true # noqa
    try:
        output = subprocess.check_output('sudo mysql -u root -e ' +
                                         '"drop database if exists cinq_tests; ' +
                                         'create database cinq_tests; ' +
                                         'grant ALL on cinq_tests.* to \'cinq_tests\'@\'localhost\' ' +
                                         'identified by \'changeme\';"',
                                         shell=True, stderr=subprocess.STDOUT)
        print(output)
    except subprocess.CalledProcessError as e:
        print(e.output)


def cleanup():
    db.session.remove()
    db.drop_all()  # Comment out to help investigate tests not cleaning up their own test data
