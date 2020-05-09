"""empty message

Revision ID: b1eb061d4c73
Revises: 6567fcfb3093
Create Date: 2020-05-09 18:58:12.741218

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b1eb061d4c73'
down_revision = '6567fcfb3093'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_disclosures_facility_association_disclosure_id', table_name='disclosures_facility_association')
    op.drop_index('ix_disclosures_facility_association_facility_id', table_name='disclosures_facility_association')
    op.drop_table('disclosures_facility_association')
    op.drop_index('ix_disclosures_disclosure_id', table_name='disclosures_disclosure')
    op.drop_index('ix_disclosures_disclosure_public_id', table_name='disclosures_disclosure')
    op.drop_index('ix_disclosures_disclosure_slug', table_name='disclosures_disclosure')
    op.drop_index('ix_disclosures_disclosure_user_id', table_name='disclosures_disclosure')
    op.drop_table('disclosures_disclosure')
    op.add_column('auth_user', sa.Column('email', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('auth_user', 'email')
    op.create_table('disclosures_disclosure',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('disclosures_disclosure_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('public_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('slug', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('date_from', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('date_to', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['auth_user.id'], name='disclosures_disclosure_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='disclosures_disclosure_pkey'),
    sa.UniqueConstraint('slug', name='disclosures_disclosure_slug_key'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_disclosures_disclosure_user_id', 'disclosures_disclosure', ['user_id'], unique=False)
    op.create_index('ix_disclosures_disclosure_slug', 'disclosures_disclosure', ['slug'], unique=True)
    op.create_index('ix_disclosures_disclosure_public_id', 'disclosures_disclosure', ['public_id'], unique=False)
    op.create_index('ix_disclosures_disclosure_id', 'disclosures_disclosure', ['id'], unique=False)
    op.create_table('disclosures_facility_association',
    sa.Column('disclosure_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('facility_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['disclosure_id'], ['disclosures_disclosure.id'], name='disclosures_facility_association_disclosure_id_fkey'),
    sa.ForeignKeyConstraint(['facility_id'], ['facilities_facility.id'], name='disclosures_facility_association_facility_id_fkey'),
    sa.UniqueConstraint('disclosure_id', 'facility_id', name='disclosures_facility_association_disclosure_id_facility_id_key')
    )
    op.create_index('ix_disclosures_facility_association_facility_id', 'disclosures_facility_association', ['facility_id'], unique=False)
    op.create_index('ix_disclosures_facility_association_disclosure_id', 'disclosures_facility_association', ['disclosure_id'], unique=False)
    # ### end Alembic commands ###
