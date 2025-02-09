"""add ondelete cascade to fk_spendings_user_id_users

Revision ID: 4f8ba080a567
Revises: 3cb5768ef949
Create Date: 2025-02-09 18:49:48.156910

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f8ba080a567"
down_revision: Union[str, None] = "3cb5768ef949"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("fk_spendings_user_id_users", "spendings", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_spendings_user_id_users"),
        "spendings",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_spendings_user_id_users"), "spendings", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_spendings_user_id_users", "spendings", "users", ["user_id"], ["id"]
    )
