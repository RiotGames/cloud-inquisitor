import copy

from flask import session, current_app

from cloud_inquisitor import AWS_REGIONS, CINQ_PLUGINS
from cloud_inquisitor.constants import ROLE_ADMIN, ROLE_USER, PLUGIN_NAMESPACES
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.accounts import BaseAccount
from cloud_inquisitor.utils import has_access, to_camelcase
from cloud_inquisitor.wrappers import check_auth, rollback


class MetaData(BaseView):
    URLS = ['/api/v1/metadata']

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        _, accts = BaseAccount.search(account_ids=session['accounts'])
        accounts = [acct.to_json(is_admin=ROLE_ADMIN in session['user'].roles) for acct in accts]
        account_types = list(self.__get_account_types())

        menu_items = {}
        groups = sorted(current_app.menu_items, key=lambda x: (
            current_app.menu_items[x]['order'], current_app.menu_items[x]['name']
        ))

        for groupName in groups:
            group = current_app.menu_items[groupName]

            if has_access(session['user'], group['required_role']):
                menu_items[groupName] = copy.deepcopy(current_app.menu_items[groupName])

        return self.make_response({
            'accounts': accounts,
            'regions': list(AWS_REGIONS),
            'menuItems': menu_items,
            'accountTypes': account_types,
            'resourceTypes': {v.resource_name: k for k, v in current_app.types.items()},
            'currentUser': session['user'].to_json(),
            'notifiers': [{'type': k, 'validation': v} for k, v in current_app.notifiers.items()],
        })

    def __get_account_types(self):
        for entry_point in CINQ_PLUGINS[PLUGIN_NAMESPACES['accounts']]['plugins']:
            cls = entry_point.load()
            yield {
                'name': cls.account_type,
                'properties': [
                    {key: to_camelcase(value) if key == 'key' else value for key, value in prop.items()}
                        for prop in cls.class_properties
                ]
            }
