"""Upgrade account contacts to new format

Revision ID: e2de0ea03287
Revises: e445d703e60f
Create Date: 2018-03-19 14:52:35.411130

"""
import json

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = 'e2de0ea03287'
down_revision = 'e445d703e60f'


def upgrade():
    conn = op.get_bind()
    res = conn.execute('SELECT account_id, account_name, contacts FROM accounts')
    for account_id, account_name, contacts in res:
        new_contacts = []
        contacts = json.loads(contacts)
        for contact in contacts:
            if type(contact) == dict:
                new_contacts.append(contact)
            else:
                new_contacts.append({
                    'type': 'slack' if contact.startswith('#') else 'email',
                    'value': contact
                })

        if new_contacts != contacts:
            print('Updating contacts for {} ({})'.format(account_name, account_id))
            conn.execute(
                sa.sql.text('UPDATE accounts SET contacts = :contacts WHERE account_id = :account_id'),
                {
                    'account_id': account_id,
                    'contacts': json.dumps(new_contacts)
                }
            )


def downgrade():
    conn = op.get_bind()
    res = conn.execute('SELECT account_id, account_name, contacts FROM accounts')
    for account_id, account_name, contacts in res:
        new_contacts = []
        contacts = json.loads(contacts)
        for contact in contacts:
            if type(contact) == dict:
                new_contacts.append(contact['value'])
            else:
                new_contacts.append(contact)

        if new_contacts != contacts:
            print('Updating contacts for {} ({})'.format(account_name, account_id))
            conn.execute(
                sa.sql.text('UPDATE accounts SET contacts = :contacts WHERE account_id = :account_id'),
                {
                    'account_id': account_id,
                    'contacts': json.dumps(new_contacts)
                }
            )
