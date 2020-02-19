"""empty message

Revision ID: 0eaf360f4cd5
Revises: a94e27e6bfe2
Create Date: 2020-02-18 10:25:42.792066

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0eaf360f4cd5'
down_revision = 'a94e27e6bfe2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('wedding_registries', sa.Column('bride_first_name', sa.String(length=100), nullable=False))
    op.add_column('wedding_registries', sa.Column('bride_last_name', sa.String(length=100), nullable=False))
    op.add_column('wedding_registries', sa.Column('groom_first_name', sa.String(length=100), nullable=False))
    op.add_column('wedding_registries', sa.Column('groom_last_name', sa.String(length=100), nullable=False))
    op.drop_column('wedding_registries', 'spouse_first_name')
    op.drop_column('wedding_registries', 'last_name')
    op.drop_column('wedding_registries', 'first_name')
    op.drop_column('wedding_registries', 'spouse_last_name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('wedding_registries', sa.Column('spouse_last_name', mysql.VARCHAR(collation='utf8mb4_general_ci', length=100), nullable=False))
    op.add_column('wedding_registries', sa.Column('first_name', mysql.VARCHAR(collation='utf8mb4_general_ci', length=100), nullable=False))
    op.add_column('wedding_registries', sa.Column('last_name', mysql.VARCHAR(collation='utf8mb4_general_ci', length=100), nullable=False))
    op.add_column('wedding_registries', sa.Column('spouse_first_name', mysql.VARCHAR(collation='utf8mb4_general_ci', length=100), nullable=False))
    op.drop_column('wedding_registries', 'groom_last_name')
    op.drop_column('wedding_registries', 'groom_first_name')
    op.drop_column('wedding_registries', 'bride_last_name')
    op.drop_column('wedding_registries', 'bride_first_name')
    # ### end Alembic commands ###