"""add spending_categories table

Revision ID: cd5155f35f7b
Revises: 9b1a31d39e27
Create Date: 2025-02-08 16:37:49.175507

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cd5155f35f7b"
down_revision: Union[str, None] = "9b1a31d39e27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "spending_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spending_categories")),
    )
    op.create_index(
        op.f("ix_spending_categories_name"),
        "spending_categories",
        ["name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_spending_categories_name"), table_name="spending_categories")
    op.drop_table("spending_categories")
