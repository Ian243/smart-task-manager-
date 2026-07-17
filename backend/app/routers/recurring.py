from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.recurring import (
    PaginatedRecurringTaskResponse,
    RecurringTaskCreate,
    RecurringTaskResponse,
)
from app.schemas.task import TaskResponse
from app.services import recurring as recurring_service

router = APIRouter(prefix="/recurring", tags=["recurring"])


@router.post("", response_model=RecurringTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_in: RecurringTaskCreate,
    current_user: User = Depends(require_role(UserRole.MANAGER)),
    session: AsyncSession = Depends(get_db)
):
    """
    Create a new recurring task template.
    Only managers can create these for now, per simple RBAC.
    """
    return await recurring_service.create_template(session, template_in, current_user)


@router.get("", response_model=PaginatedRecurringTaskResponse)
async def get_templates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    List recurring templates.
    """
    skip = (page - 1) * size
    total, items = await recurring_service.get_templates(
        session=session, skip=skip, limit=size, current_user=current_user
    )
    return PaginatedRecurringTaskResponse(total=total, page=page, size=size, items=items)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(require_role(UserRole.MANAGER)),
    session: AsyncSession = Depends(get_db)
):
    """
    Delete a recurring task template.
    """
    await recurring_service.delete_template(session, template_id, current_user)


@router.post("/generate", response_model=list[TaskResponse])
async def generate_due_tasks(
    current_user: User = Depends(require_role(UserRole.MANAGER)),
    session: AsyncSession = Depends(get_db)
):
    """
    Generates tasks from due templates.
    Intended to be hit by n8n using X-API-Key (which assumes MANAGER role).
    """
    return await recurring_service.generate_due_tasks(session)
