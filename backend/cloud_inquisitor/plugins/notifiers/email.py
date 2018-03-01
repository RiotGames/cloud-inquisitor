"""Email based notification system"""
import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cloud_inquisitor import get_local_aws_session
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.constants import NS_EMAIL
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import EmailSendError
from cloud_inquisitor.plugins.notifiers import BaseNotifier
from cloud_inquisitor.schema import Email


class EmailNotifier(BaseNotifier):
    name = 'Email Notifier'
    ns = NS_EMAIL
    options = (
        ConfigOption('enabled', True, 'bool', 'Enable the Email notifier plugin'),
        ConfigOption('from_address', 'changeme@domain.tld', 'string', 'Sender address for emails'),
        ConfigOption('method', 'ses', 'string', 'EMail sending method, either ses or smtp'),
        ConfigOption(
            'from_arn', '', 'string',
            'If using cross-account SES, this is the "From ARN", otherwise leave blank'
        ),
        ConfigOption(
            'return_path_arn', '', 'string',
            'If using cross-account SES, this is the "Return Path ARN", otherwise leave blank'
        ),
        ConfigOption(
            'source_arn', '', 'string',
            'If using cross-account SES, this is the "Source ARN", otherwise leave blank'
        ),
        ConfigOption('ses_region', 'us-west-2', 'string', 'Which SES region to send emails from'),
        ConfigOption('smtp_server', 'localhost', 'string', 'Address of the SMTP server to use'),
        ConfigOption('smtp_port', 25, 'int', 'Port for the SMTP server'),
        ConfigOption(
            'smtp_username', '', 'string',
            'Username for SMTP authentication. Leave blank for no authentication'
        ),
        ConfigOption(
            'smtp_password', '', 'string',
            'Password for SMTP authentication. Leave blank for no authentication'
        ),
        ConfigOption('smtp_tls', False, 'bool', 'Use TLS for sending emails'),
    )


def send_email(subsystem, sender, recipients, subject, html_body=None, text_body=None, message_uuid=None):
    """Send an email to a list of recipients using the system configured email method (SES or SMTP)

    Args:
        subsystem (str): Name of the subsystem where the email originated from
        sender (str): From email address
        recipients (`list` of `str`): List of recipient email addresses
        subject (str): Subject of the email
        html_body (str): HTML body of the email
        text_body (str): Text body of the email
        message_uuid (str): Optional UUID message identifier. If not provided one will be generated automatically

    Returns:
        `None`
    """
    if not html_body and not text_body:
        raise ValueError('Either html_body or text_body must be supplied')

    # Remove dupes from the recipients list
    if type(recipients) == str:
        recipients = [recipients]

    recipients = list(set(recipients))

    email = Email()
    email.timestamp = datetime.now()
    email.subsystem = subsystem
    email.sender = sender
    email.recipients = recipients
    email.subject = subject
    email.uuid = message_uuid or uuid.uuid4()
    email.message_html = html_body
    email.message_text = text_body

    db.session.add(email)
    db.session.commit()

    method = dbconfig.get('method', NS_EMAIL, 'ses')
    try:
        if method == 'ses':
            __send_ses_email(sender, recipients, subject, html_body, text_body)

        elif method == 'smtp':
            __send_smtp_email(sender, recipients, subject, html_body, text_body)

        else:
            raise ValueError('Invalid email method: {}'.format(method))
    except Exception as ex:
        raise EmailSendError(ex)


def __send_ses_email(sender, recipients, subject, html_body, text_body):
    """Send an email using SES

    Args:
        sender (str): From email address
        recipients (`1ist` of `str`): List of recipient email addresses
        subject (str): Subject of the email
        html_body (str): HTML body of the email
        text_body (str): Text body of the email

    Returns:
        `None`
    """
    source_arn = dbconfig.get('source_arn', NS_EMAIL)
    return_arn = dbconfig.get('return_path_arn', NS_EMAIL)

    session = get_local_aws_session()
    ses = session.client('ses', region_name=dbconfig.get('ses_region', NS_EMAIL, 'us-west-2'))

    body = {}
    if html_body:
        body['Html'] = {
            'Data': html_body
        }
    if text_body:
        body['Text'] = {
            'Data': text_body
        }

    ses_options = {
        'Source': sender,
        'Destination': {
            'ToAddresses': recipients
        },
        'Message': {
            'Subject': {
                'Data': subject
            },
            'Body': body
        }
    }

    # Set SES options if needed
    if source_arn and return_arn:
        ses_options.update({
            'SourceArn': source_arn,
            'ReturnPathArn': return_arn
        })

    ses.send_email(**ses_options)


def __send_smtp_email(sender, recipients, subject, html_body, text_body):
    """Send an email using SMTP

    Args:
        sender (str): From email address
        recipients (`list` of `str`): List of recipient email addresses
        subject (str): Subject of the email
        html_body (str): HTML body of the email
        text_body (str): Text body of the email

    Returns:
        `None`
    """
    smtp = smtplib.SMTP(
        dbconfig.get('smtp_server', NS_EMAIL, 'localhost'),
        dbconfig.get('smtp_port', NS_EMAIL, 25)
    )
    source_arn = dbconfig.get('source_arn', NS_EMAIL)
    return_arn = dbconfig.get('return_path_arn', NS_EMAIL)
    from_arn = dbconfig.get('from_arn', NS_EMAIL)
    msg = MIMEMultipart('alternative')

    # Set SES options if needed
    if source_arn and from_arn and return_arn:
        msg['X-SES-SOURCE-ARN'] = source_arn
        msg['X-SES-FROM-ARN'] = from_arn
        msg['X-SES-RETURN-PATH-ARN'] = return_arn

    msg['Subject'] = subject
    msg['To'] = ','.join(recipients)
    msg['From'] = sender

    # Check body types to avoid exceptions
    if html_body:
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
    if text_body:
        text_part = MIMEText(text_body, 'plain')
        msg.attach(text_part)

    # TLS if needed
    if dbconfig.get('smtp_tls', NS_EMAIL, False):
        smtp.starttls()

    # Login if needed
    username = dbconfig.get('smtp_username', NS_EMAIL)
    password = dbconfig.get('smtp_password', NS_EMAIL)
    if username and password:
        smtp.login(username, password)

    smtp.sendmail(sender, recipients, msg.as_string())
    smtp.quit()
