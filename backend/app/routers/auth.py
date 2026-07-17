"""
Authentication router. Endpoints for registration, login, token refresh, and profile fetching.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, get_current_user
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserResponse
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, 
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """Register a new user."""
    user = await auth_service.get_user_by_email(session, user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    return await auth_service.register_user(session, user_in, role=user_in.role)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    """OAuth2 compatible token login, getting an access and refresh token."""
    user = await auth_service.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get the currently logged-in user profile."""
    return current_user


@router.get("/users", response_model=list[UserResponse])
async def get_users(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """Get all users for dropdowns."""
    return await auth_service.get_all_users(session)
