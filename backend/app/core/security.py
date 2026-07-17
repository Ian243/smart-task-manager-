"""
Security utilities: Password hashing, JWT generation, and FastAPI dependencies for auth.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for extracting token from header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash from a password."""
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, role: UserRole, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access JWT embedding the user ID (sub) and role."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    # We embed the role so that simple role checks don't require a DB lookup
    to_encode = {"exp": expire, "sub": str(subject), "role": role.value}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Create a longer-lived refresh JWT."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    api_key: Annotated[str | None, Depends(api_key_header)],
    db=Depends(get_db)
) -> User:
    """
    Dependency that decodes the JWT, extracts the user ID, and fetches the user from the DB.
    Alternatively, accepts an X-API-Key for internal system access (n8n).
    Raises 401 if tokens are invalid or user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if api_key and api_key == settings.n8n_shared_secret:
        import uuid
        return User(
            id=uuid.UUID(int=0), 
            email="n8n@system", 
            name="n8n System", 
            role=UserRole.MANAGER, 
            password_hash=""
        )
        
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    
    session: AsyncSession = db
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user


def require_role(required_role: UserRole):
    """
    Dependency factory to enforce role-based access.
    Returns a dependency function that checks if the current user has the required role.
    """
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        # Simple hierarchy: ADMIN > MANAGER > MEMBER
        roles = {UserRole.MEMBER: 1, UserRole.MANAGER: 2, UserRole.ADMIN: 3}
        
        user_role_level = roles.get(current_user.role, 0)
        required_role_level = roles.get(required_role, 0)
        
        if user_role_level < required_role_level:
            # 403 Forbidden because they are authenticated but lack permission
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
        
    return role_checker
