from slackclient import SlackClient

from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.constants import NS_SLACK
from cloud_inquisitor.exceptions import SlackError
from cloud_inquisitor.plugins.notifiers import BaseNotifier


class SlackNotifier(BaseNotifier):
    name = 'Slack Notifier'
    ns = NS_SLACK
    options = (
        ConfigOption('enabled', False, 'bool', 'Enable the Slack notifier plugin'),
        ConfigOption('api_key', '', 'string', 'API token for the slack notifications'),
        ConfigOption('bot_name', 'Inquisitor', 'string', 'Name of the bot in Slack'),
    )

    def __init__(self, api_key=None):
        super().__init__()

        if not self.enabled:
            raise SlackError('Slack messaging is disabled')

        self.slack_client = SlackClient(api_key or dbconfig.get('api_key', self.ns))
        self.bot_name = dbconfig.get('bot_name', self.ns, 'Inquisitor')

        if not self.__check():
            raise SlackError('Invalid API KEY!')

    def __check(self):
        try:
            response = self.slack_client.api_call('auth.test')
            return response['ok']
        except Exception:
            return False

    def __get_user_id(self, email):
        response = self.slack_client.api_call('users.list')
        try:
            if not response['ok']:
                raise SlackError('Failed to list Slack users!')
            for item in response['members']:
                _profile = item['profile']
                if _profile.get('email', None) == email:
                    return item['id']
            else:
                SlackError('Failed to get user from Slack!')
        except Exception as ex:
            raise SlackError(ex)

    def __get_channel_for_user(self, user_email):
        user_id = self.__get_user_id(user_email)
        try:
            response = self.slack_client.api_call('im.open', user=user_id)
            if not response['ok']:
                raise SlackError('Failed to get channel for user!')

            return response['channel']['id']
        except Exception as ex:
            raise SlackError(ex)

    def _send_message(self, target_type, target, message):
        if target_type == 'user':
            channel = self.__get_channel_for_user(target)
        else:
            channel = target

        result = self.slack_client.api_call(
            'chat.postMessage',
            channel=channel,
            text=message,
            username=self.bot_name
        )
        if not result.get('ok', False):
            raise SlackError('Failed to send message: {}'.format(result['error']))

    @staticmethod
    def send_message(contacts, message):
        """List of contacts the send the message to. You can send messages either to channels and private groups by
        using the following formats

        #channel-name
        @username-direct-message

        If the channel is the name of a private group / channel, you must first invite the bot to the channel to ensure
        it is allowed to send messages to the group.

        Returns true if the message was sent, else `False`

        Args:
            contacts (:obj:`list` of `str`,`str`): List of contacts
            message (str): Message to send

        Returns:
            `bool`
        """
        slack_api_object = SlackNotifier()

        if type(contacts) == str:
            contacts = [contacts]

        for contact in contacts:
            if contact.startswith('#'):
                target_type = 'channel'

            elif '@' in contact:
                target_type = 'user'

            else:
                raise SlackError('Unrecognized contact {}'.format(contact))

            slack_api_object._send_message(
                target_type=target_type,
                target=contact,
                message=message
            )

            return True
