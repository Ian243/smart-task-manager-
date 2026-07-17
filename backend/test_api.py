import asyncio
import httpx

async def main():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_res = await client.post(
            f"{base_url}/auth/login",
            data={"username": "manager@example.com", "password": "password123"}
        )
        print("Login:", login_res.status_code)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get me
        me_res = await client.get(f"{base_url}/auth/me", headers=headers)
        print("Me:", me_res.status_code)
        
        # 3. Get Dashboard
        dash_res = await client.get(f"{base_url}/api/v1/dashboard/summary", headers=headers)
        print("Dashboard:", dash_res.status_code, dash_res.text[:100])
        
        # 4. Create Task
        task_res = await client.post(
            f"{base_url}/api/v1/tasks/",
            headers=headers,
            json={"title": "Test Task", "priority": "high", "status": "to_do"}
        )
        print("Create Task:", task_res.status_code, task_res.text[:100])
        
        # 5. AI Chat
        ai_res = await client.post(
            f"{base_url}/api/v1/ai/chat",
            headers=headers,
            json={"message": "Can you check the status of my tasks?"}
        )
        print("AI Chat:", ai_res.status_code, ai_res.text[:100])

asyncio.run(main())
