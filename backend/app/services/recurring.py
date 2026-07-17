import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import RecurrenceCadence, TaskStatus, UserRole
from app.models.task_domain import RecurringTaskTemplate, Task
from app.models.user import User
from app.schemas.recurring import RecurringTaskCreate, RecurringTaskUpdate


async def create_template(
    session: AsyncSession, template_in: RecurringTaskCreate, current_user: User
) -> RecurringTaskTemplate:
    template = RecurringTaskTemplate(
        title_template=template_in.title_template,
        description_template=template_in.description_template,
        priority=template_in.priority,
        cadence=template_in.cadence,
        next_run_at=template_in.next_run_at,
        assignee_id=template_in.assignee_id,
        created_by=current_user.id,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    
    # Reload with relations
    stmt = (
        select(RecurringTaskTemplate)
        .options(
            selectinload(RecurringTaskTemplate.creator),
            selectinload(RecurringTaskTemplate.assignee),
        )
        .where(RecurringTaskTemplate.id == template.id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_templates(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    current_user: User = None
) -> tuple[int, Sequence[RecurringTaskTemplate]]:
    
    stmt = select(RecurringTaskTemplate).options(
        selectinload(RecurringTaskTemplate.creator),
        selectinload(RecurringTaskTemplate.assignee),
    )
    
    # Simple scoping: Managers see all, Members see only their own
    if current_user and current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        stmt = stmt.where(
            (RecurringTaskTemplate.assignee_id == current_user.id) | 
            (RecurringTaskTemplate.created_by == current_user.id)
        )
        
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await session.scalar(count_stmt) or 0
    
    # Get paginated items
    stmt = stmt.order_by(RecurringTaskTemplate.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(stmt)
    items = result.scalars().all()
    
    return total, items


async def delete_template(session: AsyncSession, template_id: uuid.UUID, current_user: User):
    from fastapi import HTTPException
    
    stmt = select(RecurringTaskTemplate).where(RecurringTaskTemplate.id == template_id)
    result = await session.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    await session.delete(template)
    await session.commit()


async def generate_due_tasks(session: AsyncSession) -> list[Task]:
    """
    Called by an automated background trigger (via n8n).
    Finds all templates where next_run_at is <= now.
    Creates tasks for them and bumps next_run_at forward based on cadence.
    """
    now = datetime.now(timezone.utc)
    
    # Fetch due templates
    stmt = select(RecurringTaskTemplate).where(RecurringTaskTemplate.next_run_at <= now)
    result = await session.execute(stmt)
    due_templates = result.scalars().all()
    
    generated_tasks = []
    
    for tmpl in due_templates:
        # Create new task
        new_task = Task(
            title=tmpl.title_template,
            description=tmpl.description_template,
            priority=tmpl.priority,
            status=TaskStatus.TODO,
            due_date=now.date(),
            assignee_id=tmpl.assignee_id,
            created_by=tmpl.created_by,
            recurring_template_id=tmpl.id
        )
        session.add(new_task)
        generated_tasks.append(new_task)
        
        # Calculate next run
        if tmpl.cadence == RecurrenceCadence.DAILY:
            tmpl.next_run_at += timedelta(days=1)
        elif tmpl.cadence == RecurrenceCadence.WEEKLY:
            tmpl.next_run_at += timedelta(weeks=1)
        elif tmpl.cadence == RecurrenceCadence.MONTHLY:
            # Simple month bump (not accounting for end of month perfectly)
            tmpl.next_run_at += timedelta(days=30)
            
    await session.commit()
    
    # Reload generated tasks to return full objects
    if generated_tasks:
        task_ids = [t.id for t in generated_tasks]
        task_stmt = (
            select(Task)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(Task.id.in_(task_ids))
        )
        res = await session.execute(task_stmt)
        return list(res.scalars().all())
        
    return []
