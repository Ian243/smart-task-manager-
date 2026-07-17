"""
Routers for the AI agentic layer.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ParseTaskRequest,
    ParseTaskResponse,
    SuggestPriorityRequest,
    SuggestPriorityResponse,
    SummaryResponse,
)
from app.services import ai as ai_service

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/ai",
    tags=["AI Agent"],
    dependencies=[Depends(require_role(UserRole.MEMBER))],
)


@router.post("/parse-task", response_model=ParseTaskResponse)
@limiter.limit("10/minute")
async def parse_task(
    request: Request,
    payload: ParseTaskRequest,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Parse natural language into structured task fields."""
    return await ai_service.parse_task_intent(payload.text)


@router.post("/suggest-priority", response_model=SuggestPriorityResponse)
@limiter.limit("10/minute")
async def suggest_priority(
    request: Request,
    payload: SuggestPriorityRequest,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Suggest task priority based on context."""
    return await ai_service.suggest_priority(payload.title, payload.description, payload.due_date)


@router.post("/summarize/{task_id}", response_model=SummaryResponse)
@limiter.limit("10/minute")
async def summarize_task(
    request: Request,
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """Generate a summary of the task and its history."""
    return await ai_service.summarize_task(session, task_id)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_with_agent(
    request: Request,
    payload: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """Chat with the AI agent equipped with internal task tools."""
    reply = await ai_service.chat_with_agent(session, payload.message, current_user)
    return ChatResponse(reply=reply)
