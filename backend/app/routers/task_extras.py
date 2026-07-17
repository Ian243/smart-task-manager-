"""
Routers for task supplementary entities: Comments, Activity Log, and Attachments.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.task_extras import (
    ActivityLogResponse,
    AttachmentResponse,
    CommentCreate,
    CommentResponse,
)
from app.services import task_extras as task_extras_service

router = APIRouter(prefix="/tasks/{task_id}", tags=["task_extras"])


# --- Comments ---

@router.post("/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    task_id: UUID,
    comment_in: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """Add a comment to a task."""
    return await task_extras_service.add_comment(session, task_id, comment_in.body, current_user)


@router.get("/comments", response_model=list[CommentResponse])
async def get_comments(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """List all comments for a task."""
    return await task_extras_service.get_comments(session, task_id)


# --- Activity Log ---

@router.get("/activity", response_model=list[ActivityLogResponse])
async def get_activity_log(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """List activity history for a task."""
    return await task_extras_service.get_activity_log(session, task_id)


# --- Attachments ---

@router.post("/attachments", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(
    task_id: UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """Upload a file attachment to a task."""
    return await task_extras_service.upload_attachment(session, task_id, file, current_user)


@router.get("/attachments", response_model=list[AttachmentResponse])
async def get_attachments(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """List all attachments for a task."""
    return await task_extras_service.get_attachments(session, task_id)


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    task_id: UUID,
    attachment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """Download an attachment file."""
    file_path, original_filename = await task_extras_service.get_attachment_path(session, task_id, attachment_id)
    return FileResponse(path=file_path, filename=original_filename)
