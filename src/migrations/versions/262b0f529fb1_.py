"""empty message

Revision ID: 262b0f529fb1
Revises: 61b29135dba7
Create Date: 2020-08-12 13:01:44.125016

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '262b0f529fb1'
down_revision = '61b29135dba7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('agreements_agreement', sa.Column('proposal_note', sa.String(), nullable=True))
    op.add_column('agreements_agreement', sa.Column('technologies', postgresql.ARRAY(sa.String()), nullable=True))
    op.create_index(op.f('ix_agreements_agreement_technologies'), 'agreements_agreement', ['technologies'], unique=False)
    op.execute('update agreements_agreement set technologies = ARRAY[technology] where technology is not null;')
    op.drop_column('agreements_agreement', 'technology')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('agreements_agreement', sa.Column('technology', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.execute('update agreements_agreement set technology = technologies[1] where technologies is not null;')
    op.drop_column('agreements_agreement', 'proposal_note')
    op.drop_column('agreements_agreement', 'technologies')
    # ### end Alembic commands ###