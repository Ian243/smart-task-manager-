import asyncio
from app.core.database import AsyncSessionLocal
from app.services.auth import register_user
from app.schemas.auth import UserCreate
from app.models.enums import UserRole

async def seed():
    async with AsyncSessionLocal() as session:
        try:
            await register_user(session, UserCreate(name="Pallanti Asrith Vatsal", email="g19asrithvatsal@gmail.com", password="password123"), role=UserRole.MANAGER)
            print("Successfully seeded requested email.")
        except Exception as e:
            print("Error or already seeded:", e)

asyncio.run(seed())
