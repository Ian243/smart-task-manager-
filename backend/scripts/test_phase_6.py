import httpx

base_url = "http://localhost:8000"

def test():
    # 1. Login
    r = httpx.post(f"{base_url}/auth/login", data={"username": "manager@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get the first task
    r = httpx.get(f"{base_url}/tasks/", headers=headers)
    tasks = r.json()["items"]
    task_id = tasks[0]["id"]
    print(f"Using task: {task_id}")

    # 3. Assign task to trigger webhook
    r = httpx.patch(f"{base_url}/tasks/{task_id}", headers=headers, json={"assignee_id": tasks[0]["created_by"]})
    assert r.status_code == 200, r.text
    print("Task assigned (webhook fired in background)")

    # 4. Mark task completed to trigger webhook
    r = httpx.patch(f"{base_url}/tasks/{task_id}", headers=headers, json={"status": "completed"})
    assert r.status_code == 200, r.text
    print("Task completed (webhook fired in background)")

    print("Phase 6 Webhook Triggers passed successfully.")

if __name__ == "__main__":
    test()
