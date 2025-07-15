"""Create SmtpConfigs table and add next_erp_id to Products

Revision ID: c8feac5affe7
Revises: 20240315_add_user_smtp
Create Date: 2025-07-15 06:21:58.728647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8feac5affe7'
down_revision: Union[str, Sequence[str], None] = '20240315_add_user_smtp'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('SmtpConfigs',
    sa.Column('smtp_config_id', sa.Integer(), nullable=False),
    sa.Column('config_name', sa.String(), nullable=False),
    sa.Column('smtp_server', sa.String(), nullable=False),
    sa.Column('smtp_port', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('password_encrypted', sa.String(), nullable=True),
    sa.Column('use_tls', sa.Boolean(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('sender_email_address', sa.String(), nullable=False),
    sa.Column('sender_display_name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('smtp_config_id'),
    sa.UniqueConstraint('config_name')
    )
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('next_erp_id', sa.String(), nullable=True))
        batch_op.create_unique_constraint('uq_products_next_erp_id', ['next_erp_id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('uq_products_next_erp_id', type_='unique')
        batch_op.drop_column('next_erp_id')
    op.drop_table('SmtpConfigs')
