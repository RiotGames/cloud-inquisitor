"""adding issue indexes

Revision ID: 66ea04b45589
Revises: 686dbbd19b95
Create Date: 2018-02-15 11:25:47.378676

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '66ea04b45589'
down_revision = '686dbbd19b95'


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_issue_properties_issue_id'), 'issue_properties', ['issue_id'], unique=False)
    op.create_index(op.f('ix_resource_properties_resource_id'), 'resource_properties', ['resource_id'], unique=False)
    op.create_index(op.f('ix_resource_types_resource_type'), 'resource_types', ['resource_type'], unique=False)
    op.drop_index('ix_tags_key', table_name='tags')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_tags_key', 'tags', ['key'], unique=False)
    op.drop_index(op.f('ix_resource_types_resource_type'), table_name='resource_types')
    op.drop_index(op.f('ix_resource_properties_resource_id'), table_name='resource_properties')
    op.drop_index(op.f('ix_issue_properties_issue_id'), table_name='issue_properties')
    # ### end Alembic commands ###
