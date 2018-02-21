import copy

from flask import session, current_app

from cloud_inquisitor import AWS_REGIONS
from cloud_inquisitor.constants import ROLE_ADMIN, ROLE_USER
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import Account
from cloud_inquisitor.utils import has_access
from cloud_inquisitor.wrappers import check_auth, rollback


class MetaData(BaseView):
    URLS = ['/api/v1/metadata']

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        accts = db.Account.order_by('account_name').find(
            Account.account_id.in_(session['accounts'])
        )

        accounts = [acct.to_json(is_admin=ROLE_ADMIN in session['user'].roles) for acct in accts]

        menuItems = {}
        groups = sorted(current_app.menu_items, key=lambda x: (
            current_app.menu_items[x]['order'], current_app.menu_items[x]['name']
        ))

        for groupName in groups:
            group = current_app.menu_items[groupName]

            if has_access(session['user'], group['required_role']):
                menuItems[groupName] = copy.deepcopy(current_app.menu_items[groupName])

        return self.make_response({
            'accounts': accounts,
            'regions': list(AWS_REGIONS),
            'menuItems': menuItems,
            'resourceTypes': {v.resource_name: k for k, v in current_app.types.items()},
            'currentUser': session['user'].to_json()
        })
