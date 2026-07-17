from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RecurrenceCadence, TaskPriority
from app.schemas.auth import UserResponse


class RecurringTaskBase(BaseModel):
    title_template: str = Field(..., max_length=255)
    description_template: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    cadence: RecurrenceCadence
    next_run_at: datetime
    assignee_id: Optional[UUID] = None


class RecurringTaskCreate(RecurringTaskBase):
    pass


class RecurringTaskUpdate(BaseModel):
    title_template: Optional[str] = Field(None, max_length=255)
    description_template: Optional[str] = None
    priority: Optional[TaskPriority] = None
    cadence: Optional[RecurrenceCadence] = None
    next_run_at: Optional[datetime] = None
    assignee_id: Optional[UUID] = None


class RecurringTaskResponse(RecurringTaskBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    
    creator: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedRecurringTaskResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[RecurringTaskResponse]
