from io import StringIO

from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS

VALID_TAGSET = [
    {'Key': x, 'Value': 'value@example.com'} for x in dbconfig.get('required_tags', NS_AUDITOR_REQUIRED_TAGS, [])
]


def s3_upload_file_from_string(client, bucket_name, file_name, content):
    file_obj = StringIO()
    file_obj.write(content)

    client.upload_fileobj(file_obj, bucket_name, file_name)
