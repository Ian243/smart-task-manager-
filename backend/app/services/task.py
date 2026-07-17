"""
Task service containing business logic for creating, updating, listing, and soft-deleting tasks.
Enforces ownership and role-based permissions at the service layer.
"""
import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Sequence
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.enums import UserRole, TaskStatus
from app.models.task_domain import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_extras import log_activity


def check_task_update_permission(task: Task, current_user: User) -> None:
    """
    Ensure the user has permission to update the task.
    Managers can update any task.
    Members can only update tasks they created or are assigned to.
    """
    if current_user.role in (UserRole.MANAGER, UserRole.ADMIN):
        return
        
    if task.created_by == current_user.id or task.assignee_id == current_user.id:
        return
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to modify this task."
    )


async def fire_n8n_webhook(event_type: str, task_id: UUID) -> None:
    """Fire a webhook to n8n in the background."""
    settings = get_settings()
    url = settings.n8n_webhook_url
    
    async def _post():
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json={"event": event_type, "task_id": str(task_id)})
            except Exception:
                pass  # Ignore webhook failures so they don't break the user flow
                
    asyncio.create_task(_post())


async def get_task(session: AsyncSession, task_id: UUID) -> Task | None:
    """Retrieve a single task by ID, excluding soft-deleted ones."""
    stmt = select(Task).options(selectinload(Task.assignee)).where(Task.id == task_id, Task.deleted_at.is_(None))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_task(session: AsyncSession, task_in: TaskCreate, current_user: User) -> Task:
    """Create a new task. The current user is set as the creator."""
    # Members can only assign tasks to themselves
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        if task_in.assignee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members can only assign tasks to themselves."
            )
            
    new_task = Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        due_date=task_in.due_date,
        assignee_id=task_in.assignee_id,
        created_by=current_user.id
    )
    
    session.add(new_task)
    await session.flush()
    # Log task creation
    log_activity(
        session=session,
        task_id=new_task.id,
        actor_id=current_user.id,
        field_changed="task_created",
        old_value=None,
        new_value=new_task.title
    )
    
    await session.commit()
    await session.refresh(new_task)
    
    if new_task.assignee_id:
        await fire_n8n_webhook("ASSIGNED", new_task.id)
        
    # Return fully loaded task to prevent MissingGreenlet error during Pydantic serialization
    return await get_task(session, new_task.id)


async def update_task(
    session: AsyncSession, task_id: UUID, task_in: TaskUpdate, current_user: User
) -> Task:
    """Update a task if the user has permission."""
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    check_task_update_permission(task, current_user)
    
    update_data = task_in.model_dump(exclude_unset=True)
    
    # Enforce RBAC: Only the assignee can change the status
    if "status" in update_data and update_data["status"] != task.status:
        if task.assignee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned member can change the task status."
            )
            
    # Enforce RBAC: Only managers can reassign tasks or modify due dates
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        if "assignee_id" in update_data and update_data["assignee_id"] != task.assignee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can reassign tasks."
            )
        # Check if due_date is in update_data and it's actually changing
        # (pydantic might include it if it's sent in the payload)
        if "due_date" in update_data:
            # Pydantic parses dates, so we compare date objects
            new_due_date = update_data["due_date"]
            if new_due_date != task.due_date:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only managers can modify task due dates."
                )
            
    for field, value in update_data.items():
        old_value = getattr(task, field)
        if old_value != value:
            # Type cast to string safely for the log
            log_activity(
                session=session,
                task_id=task.id,
                actor_id=current_user.id,
                field_changed=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(value) if value is not None else None
            )
            setattr(task, field, value)
        
    await session.commit()
    await session.refresh(task)
    
    if "assignee_id" in update_data and update_data["assignee_id"] is not None:
        await fire_n8n_webhook("ASSIGNED", task.id)
    elif "status" in update_data and update_data["status"] == TaskStatus.COMPLETED:
        await fire_n8n_webhook("COMPLETED", task.id)
        
    # Return fully loaded task to prevent MissingGreenlet error during Pydantic serialization
    return await get_task(session, task.id)


async def delete_task(session: AsyncSession, task_id: UUID, current_user: User) -> None:
    """
    Soft-delete a task.
    Only Managers (or Admins) are allowed to delete tasks.
    """
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can delete tasks."
        )
        
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.deleted_at = datetime.now(timezone.utc)
    
    log_activity(
        session=session,
        task_id=task.id,
        actor_id=current_user.id,
        field_changed="task_deleted",
        old_value=None,
        new_value="deleted"
    )
    
    await session.commit()


async def get_tasks(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    search: Optional[str] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    is_deleted: bool = False,
    current_user: Optional[User] = None
) -> tuple[int, Sequence[Task]]:
    """
    List tasks with optional filtering, sorting, and pagination.
    Returns a tuple of (total_count, items).
    """
    if is_deleted:
        base_stmt = select(Task).where(Task.deleted_at.is_not(None))
    else:
        base_stmt = select(Task).where(Task.deleted_at.is_(None))
    
    # Scoping filter: Members only see tasks they created or are assigned to
    if current_user and current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        scoping_filter = (Task.assignee_id == current_user.id) | (Task.created_by == current_user.id)
        base_stmt = base_stmt.where(scoping_filter)
    
    # Apply filters
    if status_filter:
        base_stmt = base_stmt.where(Task.status == status_filter)
    if priority_filter:
        base_stmt = base_stmt.where(Task.priority == priority_filter)
    if assignee_id:
        base_stmt = base_stmt.where(Task.assignee_id == assignee_id)
    if search:
        # Case-insensitive search on title or description
        search_pattern = f"%{search}%"
        base_stmt = base_stmt.where(
            Task.title.ilike(search_pattern) | Task.description.ilike(search_pattern)
        )
    if due_before:
        base_stmt = base_stmt.where(Task.due_date <= due_before)
    if due_after:
        base_stmt = base_stmt.where(Task.due_date >= due_after)
        
    # Count total
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one() or 0
    
    # Get paginated items (sorting by created_at desc by default)
    items_stmt = base_stmt.options(selectinload(Task.assignee)).order_by(Task.created_at.desc()).offset(skip).limit(limit)
    items_result = await session.execute(items_stmt)
    items = items_result.scalars().all()
    
    return total, items
