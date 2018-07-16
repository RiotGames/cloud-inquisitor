"""New accounts table

Revision ID: cfb0ed4cced9
Revises: 1edcdfbc7780
Create Date: 2018-07-10 13:26:01.588708

"""
from json import dumps as to_json

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = 'cfb0ed4cced9'
down_revision = '1edcdfbc7780'

select_ai = 'SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :table'
select_cfg_item = 'SELECT value FROM config_items WHERE namespace_prefix = :ns AND `key` = :key'
select_acct_types = 'SELECT account_type_id, account_type FROM account_types'
insert_acct_type = 'INSERT INTO account_types (account_type) VALUES (:name)'
insert_acct = (
    'INSERT INTO accounts_new (account_id, account_name, account_type_id, contacts, enabled, required_roles)'
    ' VALUES(:id, :name, :type_id, :contacts, :enabled, :required_roles)'
)
insert_acct_prop = 'INSERT INTO account_properties (account_id, name, value) VALUES (:id, :name, :value)'


def upgrade():
    create_new_tables()
    migrate_data()
    switch_tables()


def downgrade():
    raise Exception('You cannot downgrade from this version')


def create_new_tables():
    op.create_table('account_types',
        sa.Column('account_type_id', mysql.INTEGER(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('account_type', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('account_type_id')
    )
    op.create_index(op.f('ix_account_types_account_type'), 'account_types', ['account_type'], unique=True)

    op.create_table('accounts_new',
        sa.Column('account_id', mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column('account_name', sa.String(length=256), nullable=False),
        sa.Column('account_type_id', mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column('contacts', mysql.JSON(), nullable=False),
        sa.Column('enabled', mysql.SMALLINT(unsigned=True), nullable=False),
        sa.Column('required_roles', mysql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ('account_type_id',),
            ['account_types.account_type_id'],
            name='fk_account_account_type_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('account_id')
    )
    op.create_index(op.f('ix_accounts_new_account_name'), 'accounts_new', ['account_name'], unique=True)
    op.create_index(op.f('ix_accounts_new_account_type_id'), 'accounts_new', ['account_type_id'], unique=False)

    op.create_table('account_properties',
        sa.Column('property_id', mysql.INTEGER(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('account_id', mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('value', mysql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ('account_id',),
            ['accounts_new.account_id'],
            name='fk_account_properties_account_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('property_id', 'account_id')
    )
    op.create_index(op.f('ix_account_properties_account_id'), 'account_properties', ['account_id'], unique=False)
    op.create_index(op.f('ix_account_properties_name'), 'account_properties', ['name'], unique=False)


def migrate_data():
    conn = op.get_bind()
    account_types = {x['account_type']: x['account_type_id'] for x in conn.execute(text(select_acct_types))}
    try:
        schema = inspect(conn.engine).default_schema_name
        conn.execute('SET FOREIGN_KEY_CHECKS=0')
        res = conn.execute(text(select_ai), {'db': schema, 'table': 'accounts'})
        acct_auto_increment = next(res)['AUTO_INCREMENT']

        for acct_type in ('AWS', 'DNS: AXFR', 'DNS: CloudFlare'):
            if acct_type not in account_types:
                conn.execute(text(insert_acct_type), {'name': acct_type})
                account_types[acct_type] = get_insert_id(conn)

        res = conn.execute('SELECT * FROM accounts')
        for acct in res:
            if acct['account_type'] == 'AWS':
                conn.execute(
                    text(insert_acct),
                    {
                        'id': acct['account_id'],
                        'name': acct['account_name'],
                        'type_id': account_types['AWS'],
                        'contacts': acct['contacts'],
                        'enabled': acct['enabled'],
                        'required_roles': acct['required_roles']
                    }
                )
                conn.execute(
                    text(insert_acct_prop),
                    {
                        'id': acct['account_id'],
                        'name': 'account_number',
                        'value': to_json(acct['account_number'])
                    }
                )

                conn.execute(
                    text(insert_acct_prop),
                    {
                        'id': acct['account_id'],
                        'name': 'ad_group_base',
                        'value': to_json(acct['ad_group_base'] or '')
                    }
                )
                print('Migrated {} account {}'.format(acct['account_type'], acct['account_name']))

            elif acct['account_type'] == 'DNS_AXFR':
                conn.execute(
                    text(insert_acct),
                    {
                        'id': acct['account_id'],
                        'name': acct['account_name'],
                        'type_id': account_types['DNS: AXFR'],
                        'contacts': acct['contacts'],
                        'enabled': acct['enabled'],
                        'required_roles': acct['required_roles']
                    }
                )
                server = get_config_value(conn, 'collector_dns', 'axfr_server')
                domains = get_config_value(conn, 'collector_dns', 'axfr_domains')

                conn.execute(text(insert_acct_prop), {'id': acct['account_id'], 'name': 'server', 'value': [server]})
                conn.execute(text(insert_acct_prop), {'id': acct['account_id'], 'name': 'domains', 'value': domains})
                print('Migrated {} account {}'.format(acct['account_type'], acct['account_name']))

            elif acct['account_type'] == 'DNS_CLOUDFLARE':
                conn.execute(
                    text(insert_acct),
                    {
                        'id': acct['account_id'],
                        'name': acct['account_name'],
                        'type_id': account_types['DNS: CloudFlare'],
                        'contacts': acct['contacts'],
                        'enabled': acct['enabled'],
                        'required_roles': acct['required_roles']
                    }
                )
                api_key = get_config_value(conn, 'collector_dns', 'cloudflare_api_key')
                email = get_config_value(conn, 'collector_dns', 'cloudflare_email')
                endpoint = get_config_value(conn, 'collector_dns', 'cloudflare_endpoint')

                conn.execute(text(insert_acct_prop), {'id': acct['account_id'], 'name': 'api_key', 'value': api_key})
                conn.execute(text(insert_acct_prop), {'id': acct['account_id'], 'name': 'email', 'value': email})
                conn.execute(text(insert_acct_prop), {'id': acct['account_id'], 'name': 'endpoint', 'value': endpoint})

                print('Migrated {} account {}'.format(acct['account_type'], acct['account_name']))

            else:
                print('Invalid account type: {}'.format(acct['account_type']))
        conn.execute(text('ALTER TABLE accounts_new AUTO_INCREMENT = :counter'), {'counter': acct_auto_increment})
    finally:
        conn.execute('SET FOREIGN_KEY_CHECKS=1')


def switch_tables():
    conn = op.get_bind()
    conn.execute('SET FOREIGN_KEY_CHECKS=0')
    conn.execute('DROP TABLE accounts')
    conn.execute('ALTER TABLE resources MODIFY `account_id` int(10) unsigned')
    conn.execute('ALTER TABLE accounts_new RENAME accounts')
    conn.execute('ALTER TABLE accounts RENAME INDEX `ix_accounts_new_account_name` TO `ix_accounts_account_name`')
    conn.execute('ALTER TABLE accounts RENAME INDEX `ix_accounts_new_account_type_id` TO `ix_accounts_account_type_id`')
    conn.execute('SET FOREIGN_KEY_CHECKS=1')


def get_insert_id(conn):
    return next(conn.execute('SELECT LAST_INSERT_ID()'))[0]


def get_config_value(conn, ns, item):
    return next(conn.execute(text(select_cfg_item), {'ns': ns, 'key': item}))['value']
