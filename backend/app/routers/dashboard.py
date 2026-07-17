"""
Routers for dashboard analytics.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get the dashboard analytics summary.
    Role-based data scoping is handled at the service layer:
    - Managers see team-wide stats.
    - Members see only stats for their assigned/created tasks.
    """
    return await dashboard_service.get_dashboard_summary(session, current_user)
