"""initial schema — users, tasks, comments, activity_log, attachments, recurring_task_templates, notifications_log

Revision ID: e60a31302c68
Revises:
Create Date: 2026-07-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e60a31302c68"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM("member", "manager", "admin", name="user_role")
task_status = postgresql.ENUM("to_do", "in_progress", "completed", name="task_status")
task_priority = postgresql.ENUM("low", "medium", "high", name="task_priority")
recurrence_cadence = postgresql.ENUM("daily", "weekly", "monthly", name="recurrence_cadence")
notification_channel = postgresql.ENUM("email", "whatsapp", name="notification_channel")
notification_status = postgresql.ENUM("pending", "sent", "failed", name="notification_status")


def upgrade() -> None:
    bind = op.get_bind()
    # Enums are created automatically by op.create_table when using postgresql.ENUM

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "recurring_task_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title_template", sa.String(255), nullable=False),
        sa.Column("description_template", sa.Text(), nullable=True),
        sa.Column("priority", task_priority, nullable=False, server_default="medium"),
        sa.Column("cadence", recurrence_cadence, nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", task_status, nullable=False, server_default="to_do"),
        sa.Column("priority", task_priority, nullable=False, server_default="medium"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "recurring_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recurring_task_templates.id"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])
    op.create_index("ix_tasks_assignee_id", "tasks", ["assignee_id"])
    op.create_index("ix_tasks_created_by", "tasks", ["created_by"])

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comments_task_id", "comments", ["task_id"])

    op.create_table(
        "activity_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("field_changed", sa.String(100), nullable=False),
        sa.Column("old_value", sa.String(255), nullable=True),
        sa.Column("new_value", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_activity_log_task_id", "activity_log", ["task_id"])

    op.create_table(
        "attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_attachments_task_id", "attachments", ["task_id"])

    op.create_table(
        "notifications_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("status", notification_status, nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_log_task_id", "notifications_log", ["task_id"])


def downgrade() -> None:
    op.drop_table("notifications_log")
    op.drop_table("attachments")
    op.drop_table("activity_log")
    op.drop_table("comments")
    op.drop_table("tasks")
    op.drop_table("recurring_task_templates")
    op.drop_table("users")

    bind = op.get_bind()
    for enum in (
        notification_status,
        notification_channel,
        recurrence_cadence,
        task_priority,
        task_status,
        user_role,
    ):
        enum.drop(bind, checkfirst=True)
