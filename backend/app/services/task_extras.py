"""
Service logic for supplementary task entities: Comments, Activity Log, and Attachments.
"""
import os
import shutil
from typing import Sequence
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.task_domain import ActivityLog, Attachment, Comment, Task
from app.models.user import User

settings = get_settings()

# --- Helpers ---

async def _verify_task_exists(session: AsyncSession, task_id: UUID) -> Task:
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# --- Comments ---

async def add_comment(
    session: AsyncSession, task_id: UUID, body: str, current_user: User
) -> Comment:
    await _verify_task_exists(session, task_id)
    
    comment = Comment(
        task_id=task_id,
        user_id=current_user.id,
        body=body
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


async def get_comments(session: AsyncSession, task_id: UUID) -> Sequence[Comment]:
    await _verify_task_exists(session, task_id)
    
    stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


# --- Activity Log ---

def log_activity(
    session: AsyncSession, 
    task_id: UUID, 
    actor_id: UUID, 
    field_changed: str, 
    old_value: str | None, 
    new_value: str | None
) -> None:
    """
    Synchronous helper to add an activity log to the session.
    Expects the caller to commit the session later.
    """
    log_entry = ActivityLog(
        task_id=task_id,
        actor_id=actor_id,
        field_changed=field_changed,
        old_value=old_value,
        new_value=new_value
    )
    session.add(log_entry)


async def get_activity_log(session: AsyncSession, task_id: UUID) -> Sequence[ActivityLog]:
    await _verify_task_exists(session, task_id)
    
    stmt = select(ActivityLog).where(ActivityLog.task_id == task_id).order_by(ActivityLog.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


# --- Attachments ---

async def upload_attachment(
    session: AsyncSession, task_id: UUID, file: UploadFile, current_user: User
) -> Attachment:
    await _verify_task_exists(session, task_id)
    
    # Ensure upload directory exists
    os.makedirs(settings.local_storage_path, exist_ok=True)
    
    # Generate unique filename to prevent collisions
    unique_filename = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(settings.local_storage_path, unique_filename)
    
    # Save file to local disk (in a production environment, this would go to S3)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    size = os.path.getsize(file_path)
    
    attachment = Attachment(
        task_id=task_id,
        uploaded_by=current_user.id,
        file_name=file.filename,
        storage_path=file_path,
        mime_type=file.content_type or "application/octet-stream",
        size=size
    )
    
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    return attachment


async def get_attachments(session: AsyncSession, task_id: UUID) -> Sequence[Attachment]:
    await _verify_task_exists(session, task_id)
    
    stmt = select(Attachment).where(Attachment.task_id == task_id).order_by(Attachment.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_attachment_path(session: AsyncSession, task_id: UUID, attachment_id: UUID) -> tuple[str, str]:
    """Returns (file_path, original_file_name) for download."""
    await _verify_task_exists(session, task_id)
    
    stmt = select(Attachment).where(Attachment.id == attachment_id, Attachment.task_id == task_id)
    result = await session.execute(stmt)
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
        
    if not os.path.exists(attachment.storage_path):
        raise HTTPException(status_code=404, detail="File physically missing from storage")
        
    return attachment.storage_path, attachment.file_name
