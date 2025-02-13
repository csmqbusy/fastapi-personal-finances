"""add category_name field in users_spending_categories table

Revision ID: b0871fcfa8d2
Revises: f0e27e103ec1
Create Date: 2025-02-13 12:17:20.647245

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b0871fcfa8d2"
down_revision: Union[str, None] = "f0e27e103ec1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users_spending_categories",
        sa.Column("category_name", sa.String(), nullable=False),
    )
    op.create_unique_constraint(
        "uq_user_category", "users_spending_categories", ["user_id", "category_name"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_category", "users_spending_categories", type_="unique")
    op.drop_column("users_spending_categories", "category_name")
