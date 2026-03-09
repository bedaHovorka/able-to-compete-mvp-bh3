"""Add priority to cards

Revision ID: a1b2c3d4e5f6
Revises: 53039e94c242
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "53039e94c242"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    cardpriority = sa.Enum("low", "medium", "high", "critical", name="cardpriority")
    cardpriority.create(op.get_bind(), checkfirst=True)

    # Add priority column with default 'medium' (backfills existing rows automatically)
    op.add_column(
        "cards",
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", "critical", name="cardpriority"),
            nullable=False,
            server_default="medium",
        ),
    )


def downgrade() -> None:
    op.drop_column("cards", "priority")

    # Drop the enum type
    cardpriority = sa.Enum("low", "medium", "high", "critical", name="cardpriority")
    cardpriority.drop(op.get_bind(), checkfirst=True)
