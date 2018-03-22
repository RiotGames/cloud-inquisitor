"""Email based notification system"""
import re
import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cloud_inquisitor import get_local_aws_session
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.constants import NS_EMAIL, RGX_EMAIL_VALIDATION_PATTERN
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import EmailSendError
from cloud_inquisitor.plugins.notifiers import BaseNotifier
from cloud_inquisitor.schema import Email
from cloud_inquisitor.utils import send_notification, NotificationContact, deprecated


class EmailNotifier(BaseNotifier):
    name = 'Email Notifier'
    ns = NS_EMAIL
    notifier_type = 'email'
    validation = RGX_EMAIL_VALIDATION_PATTERN
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

    def __init__(self):
        super().__init__()
        self.sender = self.dbconfig.get('from_address', NS_EMAIL)

    def notify(self, subsystem, recipient, subject, body_html, body_text):
        """Method to send a notification. A plugin may use only part of the information, but all fields are required.

        Args:
            subsystem (`str`): Name of the subsystem originating the notification
            recipient (`str`): Recipient email address
            subject (`str`): Subject / title of the notification
            body_html (`str)`: HTML formatted version of the message
            body_text (`str`): Text formatted version of the message

        Returns:
            `None`
        """
        if not re.match(RGX_EMAIL_VALIDATION_PATTERN, recipient, re.I):
            raise ValueError('Invalid recipient provided')

        email = Email()
        email.timestamp = datetime.now()
        email.subsystem = subsystem
        email.sender = self.sender
        email.recipients = recipient
        email.subject = subject
        email.uuid = uuid.uuid4()
        email.message_html = body_html
        email.message_text = body_text

        method = dbconfig.get('method', NS_EMAIL, 'ses')
        try:
            if method == 'ses':
                self.__send_ses_email([recipient], subject, body_html, body_text)

            elif method == 'smtp':
                self.__send_smtp_email([recipient], subject, body_html, body_text)

            else:
                raise ValueError('Invalid email method: {}'.format(method))

            db.session.add(email)
            db.session.commit()
        except Exception as ex:
            raise EmailSendError(ex)

    def __send_ses_email(self, recipients, subject, body_html, body_text):
        """Send an email using SES

        Args:
            recipients (`1ist` of `str`): List of recipient email addresses
            subject (str): Subject of the email
            body_html (str): HTML body of the email
            body_text (str): Text body of the email

        Returns:
            `None`
        """
        source_arn = dbconfig.get('source_arn', NS_EMAIL)
        return_arn = dbconfig.get('return_path_arn', NS_EMAIL)

        session = get_local_aws_session()
        ses = session.client('ses', region_name=dbconfig.get('ses_region', NS_EMAIL, 'us-west-2'))

        body = {}
        if body_html:
            body['Html'] = {
                'Data': body_html
            }
        if body_text:
            body['Text'] = {
                'Data': body_text
            }

        ses_options = {
            'Source': self.sender,
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

    def __send_smtp_email(self, recipients, subject, html_body, text_body):
        """Send an email using SMTP

        Args:
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
        msg['From'] = self.sender

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

        smtp.sendmail(self.sender, recipients, msg.as_string())
        smtp.quit()


@deprecated('send_email has been deprecated, use cloud_inquisitor.utils.send_notifications instead')
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
    if type(recipients) == str:
        recipients = [recipients]

    recipients = list(set(recipients))

    send_notification(
        subsystem=subsystem,
        recipients=[NotificationContact('email', x) for x in recipients],
        subject=subject,
        body_html=html_body,
        body_text=text_body
    )
