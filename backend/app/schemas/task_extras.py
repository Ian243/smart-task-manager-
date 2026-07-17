"""
Schemas for task supplementary entities: Comments, Activity Logs, and Attachments.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Comments ---

class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    id: UUID
    task_id: UUID
    user_id: UUID
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Activity Log ---

class ActivityLogResponse(BaseModel):
    id: UUID
    task_id: UUID
    actor_id: UUID
    field_changed: str
    old_value: str | None = None
    new_value: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Attachments ---

class AttachmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    uploaded_by: UUID
    file_name: str
    storage_path: str
    mime_type: str
    size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
