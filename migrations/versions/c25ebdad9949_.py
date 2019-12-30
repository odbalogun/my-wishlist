"""empty message

Revision ID: c25ebdad9949
Revises: 3bd4bab81bb4
Create Date: 2019-12-21 09:46:23.389705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c25ebdad9949'
down_revision = '3bd4bab81bb4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('registries', sa.Column('is_active', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('registries', 'is_active')
    # ### end Alembic commands ###