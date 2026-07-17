"""
Authentication services. Business logic for user registration and credential verification.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserCreate


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Retrieve a user by their email address."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_all_users(session: AsyncSession):
    """Retrieve all users."""
    result = await session.execute(select(User))
    return result.scalars().all()


async def register_user(session: AsyncSession, user_in: UserCreate, role: UserRole = UserRole.MEMBER) -> User:
    """Hash password and create a new user record."""
    hashed_password = get_password_hash(user_in.password)
    
    new_user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=hashed_password,
        role=role
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    """Verify credentials and return the user if valid."""
    user = await get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
