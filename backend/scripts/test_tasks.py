import httpx

base_url = "http://localhost:8000"

def test():
    # 1. Login
    r = httpx.post(f"{base_url}/auth/login", data={"username": "manager@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    print(f"Got token: {token[:10]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a task
    r = httpx.post(
        f"{base_url}/tasks/",
        headers=headers,
        json={"title": "First Test Task", "description": "Testing CRUD", "priority": "high"}
    )
    assert r.status_code == 201, r.text
    task = r.json()
    print(f"Created task: {task['id']}")

    # 3. Get tasks
    r = httpx.get(f"{base_url}/tasks/", headers=headers)
    assert r.status_code == 200, r.text
    tasks = r.json()["items"]
    print(f"Total tasks: {len(tasks)}")

    print("Tests passed successfully.")

if __name__ == "__main__":
    test()
