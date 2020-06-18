"""empty message

Revision ID: 1ec978d38bb7
Revises: a04d9ab484c9
Create Date: 2020-06-04 06:36:33.831636

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ec978d38bb7'
down_revision = 'a04d9ab484c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('auth_user', 'is_importing_facilities')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('auth_user', sa.Column('is_importing_facilities', sa.BOOLEAN(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###