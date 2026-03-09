"""Add composite index on checks (monitor_id, checked_at)

Revision ID: a1b2c3d4e5f6
Revises: 53039e94c242
Create Date: 2026-03-09 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "53039e94c242"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_check_monitor_checked_at", "checks", ["monitor_id", "checked_at"])


def downgrade() -> None:
    op.drop_index("ix_check_monitor_checked_at", table_name="checks")
