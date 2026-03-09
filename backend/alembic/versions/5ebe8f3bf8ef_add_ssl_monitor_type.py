"""add_ssl_monitor_type

Revision ID: 5ebe8f3bf8ef
Revises: 53039e94c242
Create Date: 2026-03-09 20:00:00.000000

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5ebe8f3bf8ef"
down_revision: Union[str, None] = "53039e94c242"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL does not allow ALTER TYPE ... ADD VALUE inside a transaction.
    # Use AUTOCOMMIT isolation level to allow the enum value addition.
    connection = op.get_bind()
    connection = connection.execution_options(isolation_level="AUTOCOMMIT")
    connection.execute(sa.text("ALTER TYPE monitortype ADD VALUE IF NOT EXISTS 'ssl'"))


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; this is a no-op.
    pass
