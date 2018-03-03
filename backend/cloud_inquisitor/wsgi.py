from cloud_inquisitor.app import create_app
from cloud_inquisitor.log import setup_logging


def run():
    setup_logging()
    app = create_app()
    app.register_plugins()
    return app
