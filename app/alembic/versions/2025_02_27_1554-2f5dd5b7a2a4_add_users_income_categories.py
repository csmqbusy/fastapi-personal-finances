"""add users_income_categories

Revision ID: 2f5dd5b7a2a4
Revises: 0fd9019002c1
Create Date: 2025-02-27 15:54:21.388438

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f5dd5b7a2a4"
down_revision: Union[str, None] = "0fd9019002c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users_income_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_name", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_users_income_categories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users_income_categories")),
        sa.UniqueConstraint("user_id", "category_name", name="uq_user_income_category"),
    )


def downgrade() -> None:
    op.drop_table("users_income_categories")
