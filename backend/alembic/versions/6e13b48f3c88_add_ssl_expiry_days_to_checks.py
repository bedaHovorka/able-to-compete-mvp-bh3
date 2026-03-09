"""add_ssl_expiry_days_to_checks

Revision ID: 6e13b48f3c88
Revises: 5ebe8f3bf8ef
Create Date: 2026-03-09 20:01:00.000000

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6e13b48f3c88"
down_revision: Union[str, None] = "5ebe8f3bf8ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("checks", sa.Column("ssl_expiry_days", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("checks", "ssl_expiry_days")
