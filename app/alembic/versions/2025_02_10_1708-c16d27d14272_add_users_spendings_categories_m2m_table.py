"""add users_spendings_categories m2m table

Revision ID: c16d27d14272
Revises: 4f8ba080a567
Create Date: 2025-02-10 17:08:06.809055

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c16d27d14272"
down_revision: Union[str, None] = "4f8ba080a567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users_spending_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users_spending_categories")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["spending_categories.id"],
            name=op.f("fk_users_spending_categories_category_id_spending_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_users_spending_categories_user_id_users"),
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("users_spending_categories")
