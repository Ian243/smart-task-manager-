"""
Task-related schemas for request validation and response serialization.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskPriority, TaskStatus
from app.schemas.auth import UserResponse



class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    assignee_id: Optional[UUID] = None


class TaskCreate(TaskBase):
    assignee_id: UUID


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    assignee_id: Optional[UUID] = None


class TaskResponse(TaskBase):
    id: UUID
    created_by: UUID
    recurring_template_id: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    assignee: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedTaskResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[TaskResponse]
