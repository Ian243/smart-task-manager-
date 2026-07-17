from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda obj: [e.value for e in obj]), 
        default=UserRole.MEMBER, nullable=False
    )

    # Tasks this user created vs. is assigned to are two distinct relationships,
    # disambiguated via foreign_keys since both point at the tasks table.
    created_tasks = relationship(
        "Task", foreign_keys="Task.created_by", back_populates="creator"
    )
    assigned_tasks = relationship(
        "Task", foreign_keys="Task.assignee_id", back_populates="assignee"
    )
    comments = relationship("Comment", back_populates="author")
    activity_entries = relationship("ActivityLog", back_populates="actor")
    attachments = relationship("Attachment", back_populates="uploader")
    recurring_templates = relationship(
        "RecurringTaskTemplate", foreign_keys="RecurringTaskTemplate.created_by", back_populates="creator"
    )
    assigned_templates = relationship(
        "RecurringTaskTemplate", foreign_keys="RecurringTaskTemplate.assignee_id", back_populates="assignee"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
