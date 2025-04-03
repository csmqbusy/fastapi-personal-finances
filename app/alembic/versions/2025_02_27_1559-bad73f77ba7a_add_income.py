"""add income

Revision ID: bad73f77ba7a
Revises: 2f5dd5b7a2a4
Create Date: 2025-02-27 15:59:37.857093

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bad73f77ba7a"
down_revision: Union[str, None] = "2f5dd5b7a2a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "income",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column(
            "date",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE ('utc', now())"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["users_income_categories.id"],
            name=op.f("fk_income_category_id_users_income_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_income_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_income")),
    )


def downgrade() -> None:
    op.drop_table("income")
