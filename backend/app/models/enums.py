"""
Enums used across models. Kept as plain Python str-enums and mapped to
Postgres ENUM types — gives DB-level validation instead of relying on
application code alone to keep these values consistent.
"""
import enum


class UserRole(str, enum.Enum):
    MEMBER = "member"
    MANAGER = "manager"
    ADMIN = "admin"


class TaskStatus(str, enum.Enum):
    TODO = "to_do"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecurrenceCadence(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
