"""empty message

Revision ID: ba1745921ed4
Revises: 0eaf360f4cd5
Create Date: 2020-02-18 19:03:28.821161

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba1745921ed4'
down_revision = '0eaf360f4cd5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('donations', sa.Column('registry_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'donations', 'wedding_registries', ['registry_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'donations', type_='foreignkey')
    op.drop_column('donations', 'registry_id')
    # ### end Alembic commands ###