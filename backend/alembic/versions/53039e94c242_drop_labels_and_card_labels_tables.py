"""Drop labels and card_labels tables

Revision ID: 53039e94c242
Revises: 89bf74ad31cb
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "53039e94c242"
down_revision: Union[str, None] = "89bf74ad31cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop association table first to satisfy foreign key constraints
    op.drop_table("card_labels")
    # Drop parent table
    op.drop_table("labels")


def downgrade() -> None:
    # Re-create labels table
    op.create_table(
        "labels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Re-create card_labels association table
    op.create_table(
        "card_labels",
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"]),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"]),
        sa.PrimaryKeyConstraint("card_id", "label_id"),
    )
