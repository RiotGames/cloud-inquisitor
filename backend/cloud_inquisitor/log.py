import json
import logging
import logging.config
import logging.handlers
import os
import traceback
from datetime import datetime

from cloud_inquisitor import app_config, config_path
from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_LOG
from cloud_inquisitor.database import db
from cloud_inquisitor.schema import LogEvent


class DBLogger(logging.Handler):
    """Class handling logging to a MySQL database
    """

    def __init__(self, min_level):
        super().__init__()
        self.min_level = min_level

    def emit(self, record):
        """Persist a record into the database

        Args:
            record (`logging.Record`): The logging.Record object to store

        Returns:
            `None`
        """
        # Skip records less than min_level
        if record.levelno < logging.getLevelName(self.min_level):
            return

        evt = LogEvent()
        evt.level = record.levelname
        evt.levelno = record.levelno
        evt.timestamp = datetime.fromtimestamp(record.created)
        evt.message = record.message
        evt.filename = record.filename
        evt.lineno = record.lineno
        evt.module = record.module
        evt.funcname = record.funcName
        evt.pathname = record.pathname
        evt.process_id = record.process

        # Only log stacktraces if its the level is ERROR or higher
        if record.levelno >= 40:
            evt.stacktrace = traceback.format_exc()

        try:
            db.session.add(evt)
            db.session.commit()
        except Exception:
            db.session.rollback()


class SyslogPipelineHandler(logging.handlers.SysLogHandler):
    """ Send logs to syslog pipeline """

    def __init__(self, address=None, facility='local7', socktype=None):
        super().__init__(
            address or (dbconfig.get('remote_syslog_server_addr', NS_LOG, '127.0.0.1'),
                        dbconfig.get('remote_syslog_server_port', NS_LOG, 514)),
            facility, socktype)

    def emit(self, record):
        if record.levelno < logging.getLevelName(dbconfig.get('log_level', NS_LOG, 'WARNING')):
            return

        super().emit(record)


class LogLevelFilter(logging.Filter):
    """Simply logging.Filter class to exclude certain log levels from the database logging tables"""
    def filter(self, record):
        return app_config.log_level == 'DEBUG' or record.levelno >= logging.getLevelName(app_config.log_level)


def setup_logging():
    """Utility function to setup the logging systems based on the `logging.json` configuration file"""

    config = json.load(open(os.path.join(config_path, 'logging.json')))
    if not dbconfig.get('enable_syslog_forwarding', NS_LOG, False):
        config['handlers']['pipeline'] = {
            'class': 'logging.NullHandler',
        }

    config['formatters']['syslog'] = {'format': json.dumps({
        'jsonEvent': 'cloud-inquisitor',
        'Event': {
            'meta': {
                'host': dbconfig.get('instance_name', default='local')
            },
            'record': {
                'time': '%(asctime)s',
                'name': '%(name)s',
                'message': '%(message)s'
            }
        }
    })}
    logging.config.dictConfig(config)
