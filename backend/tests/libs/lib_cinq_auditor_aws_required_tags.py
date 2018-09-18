from io import StringIO


def s3_upload_file_from_string(client, bucket_name, file_name, content):
    file_obj = StringIO()
    file_obj.write(content)

    client.upload_fileobj(file_obj, bucket_name, file_name)
