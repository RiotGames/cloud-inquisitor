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
from cloud_inquisitor.schema import LogEvent, AuditLog
from cloud_inquisitor.utils import get_template

_AUDIT_LOGGER = logging.getLogger('audit-log')


class DBLogger(logging.Handler):
    """Class handling logging to a MySQL database"""
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
    """ Send logs to a syslog server"""
    def __init__(self, address=None, facility='local7', socktype=None):
        super().__init__(
            address or (
                dbconfig.get('remote_syslog_server_addr', NS_LOG, '127.0.0.1'),
                int(dbconfig.get('remote_syslog_server_port', NS_LOG, 514))
            ),
            facility,
            socktype
        )


class LogLevelFilter(logging.Filter):
    """Simply logging.Filter class to exclude certain log levels from the database logging tables"""
    def filter(self, record):
        return app_config.log_level == 'DEBUG' or record.levelno >= logging.getLevelName(app_config.log_level)


def _get_syslog_format(event_type):
    """Take an event type argument and return a python logging format

    In order to properly format the syslog messages to current standard, load the template and perform necessary
    replacements and return the string.

    Args:
        event_type (str): Event type name

    Returns:
        `str`
    """
    syslog_format_template = get_template('syslog_format.json')
    fmt = syslog_format_template.render(
        event_type=event_type,
        host=dbconfig.get('instance_name', default='local')
    )

    # Load and redump string, to get rid of any extraneous whitespaces
    return json.dumps(json.loads(fmt))


def setup_logging():
    """Utility function to setup the logging systems based on the `logging.json` configuration file"""
    config = json.load(open(os.path.join(config_path, 'logging.json')))

    # If syslogging is disabled, set the pipeline handler to NullHandler
    if dbconfig.get('enable_syslog_forwarding', NS_LOG, False):
        try:
            config['formatters']['syslog'] = {
                'format': _get_syslog_format('cloud-inquisitor-logs')
            }

            config['handlers']['syslog'] = {
                'class': 'cloud_inquisitor.log.SyslogPipelineHandler',
                'formatter': 'syslog',
                'filters': ['standard']
            }

            config['loggers']['cloud_inquisitor']['handlers'].append('syslog')

            # Configure the audit log handler
            audit_handler = SyslogPipelineHandler()
            audit_handler.setFormatter(logging.Formatter(_get_syslog_format('cloud-inquisitor-audit')))
            audit_handler.setLevel(logging.DEBUG)

            _AUDIT_LOGGER.addHandler(audit_handler)
            _AUDIT_LOGGER.propagate = False
        except Exception as ex:
            print('An error occured while configuring the syslogger: {}'.format(ex))

    logging.config.dictConfig(config)


def auditlog(*, event, actor, data, level=logging.INFO):
    """Generate and insert a new event

    Args:
        event (`str`): Action performed
        actor (`str`): Actor (user or subsystem) triggering the event
        data (`dict`): Any extra data necessary for describing the event
        level (`str` or `int`): Log level for the message. Uses standard python logging level names / numbers

    Returns:
        `None`
    """
    try:
        entry = AuditLog()
        entry.event = event
        entry.actor = actor
        entry.data = data

        db.session.add(entry)
        db.session.commit()

        _AUDIT_LOGGER.log(
            logging.getLevelName(level) if type(level) == str else level,
            {
                'event': event,
                'actor': actor,
                'data': data,
            }
        )

    except Exception:
        logging.getLogger(__name__).exception('Failed adding audit log event')
        db.session.rollback()
