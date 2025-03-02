"""update saving_goals

Revision ID: db878de50890
Revises: 859810fdc9a8
Create Date: 2025-03-02 15:56:03.124195

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "db878de50890"
down_revision: Union[str, None] = "859810fdc9a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "saving_goals",
        "description",
        existing_type=sa.VARCHAR(length=100),
        nullable=True,
    )
    op.alter_column("saving_goals", "end_date", existing_type=sa.DATE(), nullable=True)


def downgrade() -> None:
    op.alter_column("saving_goals", "end_date", existing_type=sa.DATE(), nullable=False)
    op.alter_column(
        "saving_goals",
        "description",
        existing_type=sa.VARCHAR(length=100),
        nullable=False,
    )
