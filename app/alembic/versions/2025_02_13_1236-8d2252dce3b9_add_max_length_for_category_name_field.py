"""add max_length for category_name field

Revision ID: 8d2252dce3b9
Revises: b0871fcfa8d2
Create Date: 2025-02-13 12:36:24.336013

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8d2252dce3b9"
down_revision: Union[str, None] = "b0871fcfa8d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        'users_spending_categories', 'category_name', type_=sa.String(50))


def downgrade():
    op.alter_column(
        'users_spending_categories', 'category_name', type_=sa.String)
