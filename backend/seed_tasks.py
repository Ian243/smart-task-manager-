import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.task import TaskCreate
from app.models.enums import TaskStatus, TaskPriority
from app.services.task import create_task

async def seed_tasks():
    async with AsyncSessionLocal() as session:
        # Get users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        manager = next((u for u in users if u.role == UserRole.MANAGER), None)
        members = [u for u in users if u.role == UserRole.MEMBER]
        
        if not manager or not members:
            print("Missing manager or members. Cannot seed tasks.")
            return

        member1 = members[0]
        member2 = members[1] if len(members) > 1 else members[0]

        # Create tasks
        print("Creating tasks...")
        
        today = datetime.now(timezone.utc).date()
        
        # Task 1 for Member 1
        await create_task(
            session,
            TaskCreate(
                title="Design New Homepage",
                description="Create wireframes for the new homepage.",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                due_date=today + timedelta(days=2),
                assignee_id=member1.id
            ),
            manager
        )

        # Task 2 for Member 1
        await create_task(
            session,
            TaskCreate(
                title="Fix Login Bug",
                description="Users can't login sometimes.",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=today - timedelta(days=1), # overdue
                assignee_id=member1.id
            ),
            manager
        )

        # Task 3 for Member 2
        await create_task(
            session,
            TaskCreate(
                title="Update Documentation",
                description="Add API docs.",
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.LOW,
                due_date=today + timedelta(days=5),
                assignee_id=member2.id
            ),
            manager
        )

        # Task 4 created by Member 1 for themselves
        await create_task(
            session,
            TaskCreate(
                title="Personal Task: Clean Desk",
                description="It's a mess.",
                status=TaskStatus.TODO,
                priority=TaskPriority.LOW,
                due_date=today + timedelta(days=1),
                assignee_id=member1.id
            ),
            member1
        )
        
        print("Tasks seeded successfully!")

asyncio.run(seed_tasks())
