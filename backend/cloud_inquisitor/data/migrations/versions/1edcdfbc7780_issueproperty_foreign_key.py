"""IssueProperty foreign key

Revision ID: 1edcdfbc7780
Revises: a2e49567641a
Create Date: 2018-05-24 12:13:53.753193

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '1edcdfbc7780'
down_revision = 'a2e49567641a'


def upgrade():
    # Delete existing orphaned entries into the issue_properties tables
    op.execute('DELETE FROM issue_properties WHERE issue_id NOT IN (SELECT issue_id FROM issues)')
    op.create_foreign_key('fk_issue_properties_issue_id', 'issue_properties', 'issues', ['issue_id'], ['issue_id'], ondelete='CASCADE')


def downgrade():
    op.drop_constraint('fk_issue_properties_issue_id', 'issue_properties', type_='foreignkey')
