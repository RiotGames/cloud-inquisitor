""" new enforcements table

Revision ID: 3fca8951cd76
Revises: cfb0ed4cced9
Create Date: 2018-08-30 00:12:47.111751

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import func


# revision identifiers, used by Alembic.
revision = '3fca8951cd76'
down_revision = 'cfb0ed4cced9'


def upgrade():
    op.create_table('enforcements',
      sa.Column('enforcement_id', mysql.INTEGER(unsigned=True), nullable=False, autoincrement=True),
      sa.Column('account_id', mysql.INTEGER(unsigned=True)),
      sa.Column('resource_id', sa.String(length=256), nullable=False),
      sa.Column('action', sa.String(length=64), nullable=False),
      sa.Column('timestamp', mysql.DATETIME(timezone=False), default=func.now()),
      sa.Column('metrics', mysql.JSON()),
      sa.PrimaryKeyConstraint('enforcement_id'))

def downgrade():
    op.drop_table('enforcements')