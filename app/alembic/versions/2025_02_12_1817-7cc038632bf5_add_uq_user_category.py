"""add uq_user_category

Revision ID: 7cc038632bf5
Revises: 88884037ff38
Create Date: 2025-02-12 18:17:35.073052

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7cc038632bf5"
down_revision: Union[str, None] = "88884037ff38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_user_category", "users_spending_categories", ["user_id", "category_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_category", "users_spending_categories", type_="unique")
