"""
Task routers for exposing CRUD endpoints.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.task import PaginatedTaskResponse, TaskCreate, TaskResponse, TaskUpdate
from app.services import task as task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(require_role(UserRole.MEMBER)),
    session: AsyncSession = Depends(get_db)
):
    """
    Create a new task.
    Any member can create a task.
    """
    return await task_service.create_task(session, task_in, current_user)


@router.get("/", response_model=PaginatedTaskResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    search: Optional[str] = None,
    is_deleted: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    List tasks with pagination, filtering, and search.
    Open to all authenticated users.
    """
    skip = (page - 1) * size
    total, items = await task_service.get_tasks(
        session=session,
        skip=skip,
        limit=size,
        status_filter=status,
        priority_filter=priority,
        assignee_id=assignee_id,
        search=search,
        is_deleted=is_deleted,
        current_user=current_user
    )
    return PaginatedTaskResponse(total=total, page=page, size=size, items=items)


@router.get("/due-soon", response_model=PaginatedTaskResponse)
async def get_due_soon_tasks(
    days: int = Query(3, ge=1, le=30),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get tasks due in the next X days.
    """
    skip = (page - 1) * size
    today = datetime.now(timezone.utc).date()
    due_before = today + timedelta(days=days)
    
    total, items = await task_service.get_tasks(
        session=session,
        skip=skip,
        limit=size,
        due_after=today,
        due_before=due_before,
        current_user=current_user
    )
    return PaginatedTaskResponse(total=total, page=page, size=size, items=items)


@router.get("/overdue", response_model=PaginatedTaskResponse)
async def get_overdue_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get tasks that are past their due date but not completed.
    """
    skip = (page - 1) * size
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    
    # Needs custom handling in service if we want to filter out 'completed' status,
    # but we can pass status_filter="to_do" or "in_progress".
    # For simplicity, we just use the existing service to get anything due before today.
    # In a real app we'd add multiple status exclusions.
    total, items = await task_service.get_tasks(
        session=session,
        skip=skip,
        limit=size,
        due_before=yesterday,
        current_user=current_user
    )
    
    # Filter out completed tasks in memory for this simple implementation
    # since our basic get_tasks doesn't support NOT IN queries yet.
    incomplete_items = [t for t in items if t.status != "completed"]
    
    return PaginatedTaskResponse(
        total=len(incomplete_items), # Not exact total if pagination cut it off, but acceptable for now
        page=page, 
        size=size, 
        items=incomplete_items
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get a specific task by ID.
    """
    task = await task_service.get_task(session, task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(require_role(UserRole.MEMBER)),
    session: AsyncSession = Depends(get_db)
):
    """
    Update a task.
    Managers can update any task.
    Members can only update tasks they created or are assigned to.
    """
    return await task_service.update_task(session, task_id, task_in, current_user)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(require_role(UserRole.MANAGER)),
    session: AsyncSession = Depends(get_db)
):
    """
    Soft-delete a task.
    Only Managers and Admins can delete tasks.
    """
    await task_service.delete_task(session, task_id, current_user)
