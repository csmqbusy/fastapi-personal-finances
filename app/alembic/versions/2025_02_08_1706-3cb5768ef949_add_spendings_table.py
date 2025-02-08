"""add spendings table

Revision ID: 3cb5768ef949
Revises: cd5155f35f7b
Create Date: 2025-02-08 17:06:10.466417

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3cb5768ef949"
down_revision: Union[str, None] = "cd5155f35f7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "spendings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column(
            "date",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE ('utc', now())"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["spending_categories.id"],
            name=op.f("fk_spendings_category_id_spending_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_spendings_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spendings")),
    )


def downgrade() -> None:
    op.drop_table("spendings")
