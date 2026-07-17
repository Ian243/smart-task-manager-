"""
Service logic for dashboard and analytics queries.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.enums import TaskStatus, UserRole
from app.models.task_domain import Task
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    PriorityCount,
    StatusCount,
    UserWorkload,
)


async def get_dashboard_summary(session: AsyncSession, current_user: User) -> DashboardSummaryResponse:
    """
    Computes analytics counts for the dashboard.
    Role-based scoping:
    - Managers get global stats.
    - Members get stats only for tasks they are assigned to or created.
    """
    
    # Base subquery filter for soft deletes
    base_filter = Task.deleted_at.is_(None)
    
    # Scoping filter
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        # Scoped to MEMBER's tasks
        scoping_filter = (Task.assignee_id == current_user.id) | (Task.created_by == current_user.id)
        base_filter = base_filter & scoping_filter
        
    # --- Total Tasks ---
    total_stmt = select(func.count()).select_from(Task).where(base_filter)
    total_result = await session.execute(total_stmt)
    total_tasks = total_result.scalar_one() or 0

    # --- Status Counts ---
    status_stmt = (
        select(Task.status, func.count(Task.id))
        .where(base_filter)
        .group_by(Task.status)
    )
    status_result = await session.execute(status_stmt)
    status_counts = [
        StatusCount(status=str(row[0].value), count=row[1]) 
        for row in status_result.all()
    ]
    
    # --- Priority Counts ---
    priority_stmt = (
        select(Task.priority, func.count(Task.id))
        .where(base_filter)
        .group_by(Task.priority)
    )
    priority_result = await session.execute(priority_stmt)
    priority_counts = [
        PriorityCount(priority=str(row[0].value), count=row[1]) 
        for row in priority_result.all()
    ]
    
    # --- Overdue Tasks ---
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    
    overdue_stmt = (
        select(func.count())
        .select_from(Task)
        .where(base_filter)
        .where(Task.status != TaskStatus.COMPLETED)
        .where(Task.due_date <= yesterday)
    )
    overdue_result = await session.execute(overdue_stmt)
    overdue_tasks = overdue_result.scalar_one() or 0
    
    # --- Due Soon Tasks (next 3 days) ---
    in_3_days = today + timedelta(days=3)
    due_soon_stmt = (
        select(func.count())
        .select_from(Task)
        .where(base_filter)
        .where(Task.status != TaskStatus.COMPLETED)
        .where(Task.due_date >= today)
        .where(Task.due_date <= in_3_days)
    )
    due_soon_result = await session.execute(due_soon_stmt)
    due_soon_tasks = due_soon_result.scalar_one() or 0

    # --- User Workload ---
    # We only care about uncompleted tasks for workload
    workload_stmt = (
        select(
            Task.assignee_id,
            User.name,
            func.count(Task.id)
        )
        .outerjoin(User, Task.assignee_id == User.id)
        .where(base_filter)
        .where(Task.status != TaskStatus.COMPLETED)
        .group_by(Task.assignee_id, User.name)
        .order_by(func.count(Task.id).desc())
    )
    workload_result = await session.execute(workload_stmt)
    user_workload = [
        UserWorkload(
            assignee_id=row[0],
            assignee_name=row[1] or "Unassigned",
            count=row[2]
        )
        for row in workload_result.all()
    ]
    
    return DashboardSummaryResponse(
        total_tasks=total_tasks,
        overdue_tasks=overdue_tasks,
        due_soon_tasks=due_soon_tasks,
        status_counts=status_counts,
        priority_counts=priority_counts,
        user_workload=user_workload
    )
