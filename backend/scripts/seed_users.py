"""
Script to seed the database with initial users (1 manager, 3 members).
Demonstrates the permission boundaries by creating distinct roles.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path to allow running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.enums import UserRole
from app.schemas.auth import UserCreate
from app.services import auth as auth_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_users():
    users_to_create = [
        {"email": "manager@example.com", "name": "Manager Bob", "password": "password123", "role": UserRole.MANAGER},
        {"email": "member1@example.com", "name": "Alice Member", "password": "password123", "role": UserRole.MEMBER},
        {"email": "member2@example.com", "name": "Charlie Member", "password": "password123", "role": UserRole.MEMBER},
        {"email": "member3@example.com", "name": "Dave Member", "password": "password123", "role": UserRole.MEMBER},
    ]

    async with AsyncSessionLocal() as session:
        for u in users_to_create:
            user = await auth_service.get_user_by_email(session, u["email"])
            if user:
                logger.info(f"User {u['email']} already exists. Skipping.")
                continue

            user_in = UserCreate(email=u["email"], name=u["name"], password=u["password"])
            await auth_service.register_user(session, user_in, role=u["role"])
            logger.info(f"Created user {u['email']} with role {u['role']}")


if __name__ == "__main__":
    asyncio.run(seed_users())
