"""
Importing every model here ensures they're all registered on Base.metadata
before Alembic (or metadata.create_all) runs — otherwise tables that are
never imported elsewhere would silently be missing from migrations.

Only two model files exist: user.py (the one entity everything else depends
on) and task_domain.py (Task + its five small dependent entities, grouped
per the file-consolidation rule in 03-coding-conventions-and-file-structure-rules.md).
"""
from app.models.task_domain import (
    ActivityLog,
    Attachment,
    Comment,
    NotificationLog,
    RecurringTaskTemplate,
    Task,
)
from app.models.user import User

__all__ = [
    "ActivityLog",
    "Attachment",
    "Comment",
    "NotificationLog",
    "RecurringTaskTemplate",
    "Task",
    "User",
]
