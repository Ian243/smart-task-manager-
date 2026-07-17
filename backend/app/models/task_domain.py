"""
Task-domain models.

Consolidated per the file-consolidation rule in
03-coding-conventions-and-file-structure-rules.md: Task, Comment,
ActivityLog, Attachment, RecurringTaskTemplate, and NotificationLog are all
small, all task-domain, and are never meaningfully used independently of
each other — so they live in one file instead of six. `User` stays in its
own file since it's the one entity every other table depends on and auth
logic will grow around it independently.

Load-bearing detail for future edits: RecurringTaskTemplate is defined
*before* Task in this file purely so Task's `recurring_template_id` FK can
reference "recurring_task_templates.id" without a forward-reference issue
at import time — the actual dependency direction is the opposite (a
template generates tasks), don't be misled by the file order.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    NotificationChannel,
    NotificationStatus,
    RecurrenceCadence,
    TaskPriority,
    TaskStatus,
)
from app.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class RecurringTaskTemplate(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """
    Not a task itself — a blueprint. The n8n 'recurring task generation'
    workflow reads rows here on a schedule and creates new Task rows from
    the template, stamping the new task's recurring_template_id back here.
    """
    __tablename__ = "recurring_task_templates"

    title_template: Mapped[str] = mapped_column(String(255), nullable=False)
    description_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority", values_callable=lambda obj: [e.value for e in obj]), default=TaskPriority.MEDIUM, nullable=False
    )
    cadence: Mapped[RecurrenceCadence] = mapped_column(
        Enum(RecurrenceCadence, name="recurrence_cadence", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    creator = relationship("User", foreign_keys=[created_by], back_populates="recurring_templates")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_templates")
    generated_tasks = relationship("Task", back_populates="recurring_template")


class Task(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """The core entity — equivalent to Jira's 'issue'."""
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", values_callable=lambda obj: [e.value for e in obj]), default=TaskStatus.TODO, nullable=False, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority", values_callable=lambda obj: [e.value for e in obj]),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # assignee_id (who does the work) and created_by (who raised it) are two
    # separate FKs to the same table — foreign_keys=[...] below is required on
    # each relationship so SQLAlchemy knows which FK maps to which side.
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    recurring_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recurring_task_templates.id"), nullable=True
    )

    # Soft delete — rows are flagged, not removed, so activity history survives "deletion"
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")
    recurring_template = relationship("RecurringTaskTemplate", back_populates="generated_tasks")

    comments = relationship(
        "Comment", back_populates="task", cascade="all, delete-orphan", order_by="Comment.created_at"
    )
    activity_log = relationship(
        "ActivityLog", back_populates="task", cascade="all, delete-orphan", order_by="ActivityLog.created_at"
    )
    attachments = relationship("Attachment", back_populates="task", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Task {self.title!r} status={self.status}>"


class Comment(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """User-authored discussion on a task — distinct from ActivityLog, which is system-authored."""
    __tablename__ = "comments"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")


class ActivityLog(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """
    System-generated record of a single field change on a task
    (e.g. status: to_do -> in_progress). One row per change — mirrors how
    Jira itself stores its change history, rather than a full-row snapshot.
    """
    __tablename__ = "activity_log"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    field_changed: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    task = relationship("Task", back_populates="activity_log")
    actor = relationship("User", back_populates="activity_entries")


class Attachment(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """
    Stores file *metadata* only — bytes live on disk (dev) or S3 (prod) per
    the storage interface in the finalized architecture doc, keeping the
    database lean regardless of file sizes.
    """
    __tablename__ = "attachments"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)

    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User", back_populates="attachments")


class NotificationLog(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """
    Written by the backend when n8n calls back after attempting a send.
    Not a stated functional requirement on its own — exists purely so the
    automation layer is auditable/demoable without digging into n8n's own
    execution history. Safe to drop if the schema needs to stay minimal.
    """
    __tablename__ = "notifications_log"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status", values_callable=lambda obj: [e.value for e in obj]),
        default=NotificationStatus.PENDING,
        nullable=False,
    )
    # A row may be created as "pending" before it's actually sent, so sent_at
    # is set later by the backend once n8n confirms the send.
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="notifications")
