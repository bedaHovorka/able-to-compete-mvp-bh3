"""Initial schema

Revision ID: 89bf74ad31cb
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "89bf74ad31cb"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # boards
    op.create_table(
        "boards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # lists
    op.create_table(
        "lists",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # cards
    op.create_table(
        "cards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("list_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["list_id"], ["lists.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # activities
    op.create_table(
        "activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # labels
    op.create_table(
        "labels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # card_labels (association table)
    op.create_table(
        "card_labels",
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"]),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"]),
        sa.PrimaryKeyConstraint("card_id", "label_id"),
    )

    # monitors
    op.create_table(
        "monitors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "type",
            sa.Enum("http", "https", "tcp", "ping", name="monitortype"),
            nullable=False,
        ),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("interval", sa.Integer(), nullable=False),
        sa.Column("timeout", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("up", "down", "degraded", "paused", name="monitorstatus"),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("expected_status_code", sa.Integer(), nullable=True),
        sa.Column("headers", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # checks
    op.create_table(
        "checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("monitor_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("up", "down", "degraded", "paused", name="monitorstatus"),
            nullable=False,
        ),
        sa.Column("response_time", sa.Float(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # incidents
    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("monitor_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "investigating", "identified", "monitoring", "resolved",
                name="incidentstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum("critical", "high", "medium", "low", name="incidentseverity"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # incident_updates
    op.create_table(
        "incident_updates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "investigating", "identified", "monitoring", "resolved",
                name="incidentstatus",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # status_pages
    op.create_table(
        "status_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("monitors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # metrics
    op.create_table(
        "metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("monitor_id", sa.Uuid(), nullable=False),
        sa.Column("uptime_percentage", sa.Float(), nullable=False),
        sa.Column("avg_response_time", sa.Float(), nullable=False),
        sa.Column("total_checks", sa.Integer(), nullable=False),
        sa.Column("failed_checks", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("metrics")
    op.drop_table("status_pages")
    op.drop_table("incident_updates")
    op.drop_table("incidents")
    op.drop_table("checks")
    op.drop_table("monitors")
    op.drop_table("card_labels")
    op.drop_table("labels")
    op.drop_table("activities")
    op.drop_table("cards")
    op.drop_table("lists")
    op.drop_table("boards")
    op.execute("DROP TYPE IF EXISTS monitortype")
    op.execute("DROP TYPE IF EXISTS monitorstatus")
    op.execute("DROP TYPE IF EXISTS incidentstatus")
    op.execute("DROP TYPE IF EXISTS incidentseverity")
