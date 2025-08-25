"""Add product_code to Product model

Revision ID: 28507734c657
Revises: 257845b76fa9
Create Date: 2025-08-25 06:17:21.948515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28507734c657'
down_revision: Union[str, Sequence[str], None] = '257845b76fa9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('product_code', sa.String(), nullable=False, server_default='DEFAULT'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('product_code')
