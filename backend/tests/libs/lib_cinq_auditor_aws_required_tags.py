from io import StringIO

from cloud_inquisitor.config import dbconfig, DBCJSON
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS

IGNORE_TAGSET = [{'Key': dbconfig.get('audit_ignore_tag', NS_AUDITOR_REQUIRED_TAGS), 'Value': 'IGNORED'}]
VALID_TAGSET = [
    {'Key': x, 'Value': 'value@example.com'} for x in dbconfig.get('required_tags', NS_AUDITOR_REQUIRED_TAGS, [])
]
VALID_TAGS = {x: 'value@example.com' for x in dbconfig.get('required_tags', NS_AUDITOR_REQUIRED_TAGS, {})}


STANDARD_ALERT_SETTINGS_STOP = 7200
STANDARD_ALERT_SETTINGS_REMOVE = 14400
STANDARD_ALERT_SETTINGS = {
    "*": {
        "stop": "{} seconds".format(STANDARD_ALERT_SETTINGS_STOP),
        "alert": ["0 seconds", "3600 seconds"],
        "scope": ["*"],
        "remove": "{} seconds".format(STANDARD_ALERT_SETTINGS_REMOVE)
    }
}


def s3_upload_file_from_string(client, bucket_name, file_name, content):
    file_obj = StringIO()
    file_obj.write(content)

    client.upload_fileobj(file_obj, bucket_name, file_name)


def set_audit_scope(*args):
    db_setting = dbconfig.get('audit_scope', NS_AUDITOR_REQUIRED_TAGS)
    db_setting['enabled'] = args
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'audit_scope', DBCJSON(db_setting))


def prep_s3_testing(cinq_test_service, collect_only=False):
    set_audit_scope('aws_s3_bucket')
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'collect_only', collect_only)
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'alert_settings', DBCJSON(STANDARD_ALERT_SETTINGS))

    cinq_test_service.start_mocking_services('cloudwatch', 's3')


def prep_rds_testing(cinq_test_service, collect_only=False):
    set_audit_scope('aws_rds_instance')
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'collect_only', collect_only)
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'alert_settings', DBCJSON(STANDARD_ALERT_SETTINGS))
