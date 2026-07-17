"""
Schemas for dashboard analytics and aggregate data.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StatusCount(BaseModel):
    status: str
    count: int


class PriorityCount(BaseModel):
    priority: str
    count: int


class UserWorkload(BaseModel):
    assignee_id: Optional[UUID]
    assignee_name: Optional[str]
    count: int


class DashboardSummaryResponse(BaseModel):
    total_tasks: int
    overdue_tasks: int
    due_soon_tasks: int
    status_counts: list[StatusCount]
    priority_counts: list[PriorityCount]
    user_workload: list[UserWorkload]

    model_config = ConfigDict(from_attributes=True)
