"""
Schemas for AI feature endpoints.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import TaskPriority


class ParseTaskRequest(BaseModel):
    text: str = Field(..., description="Natural language description of a task to create")


class ParseTaskResponse(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM


class SummaryResponse(BaseModel):
    summary: str


class SuggestPriorityRequest(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None


class SuggestPriorityResponse(BaseModel):
    suggested_priority: TaskPriority
    reasoning: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="Message for the AI agent")


class ChatResponse(BaseModel):
    reply: str
