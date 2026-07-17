import httpx
import os

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

    # 3. Add a comment
    r = httpx.post(f"{base_url}/tasks/{task_id}/comments", headers=headers, json={"body": "This is a test comment"})
    assert r.status_code == 201, r.text
    print("Comment added successfully.")

    # 4. Get comments
    r = httpx.get(f"{base_url}/tasks/{task_id}/comments", headers=headers)
    assert r.status_code == 200, r.text
    comments = r.json()
    assert len(comments) >= 1
    print(f"Total comments: {len(comments)}")

    # 5. Upload an attachment
    with open("test.txt", "w") as f:
        f.write("Hello, world!")
        
    with open("test.txt", "rb") as f:
        r = httpx.post(
            f"{base_url}/tasks/{task_id}/attachments", 
            headers=headers, 
            files={"file": ("test.txt", f, "text/plain")}
        )
    assert r.status_code == 201, r.text
    attachment = r.json()
    att_id = attachment["id"]
    print("Attachment uploaded successfully.")

    # 6. Download attachment
    r = httpx.get(f"{base_url}/tasks/{task_id}/attachments/{att_id}/download", headers=headers)
    assert r.status_code == 200, r.text
    assert r.text == "Hello, world!"
    print("Attachment downloaded successfully.")

    # 7. Update task to trigger activity log
    r = httpx.patch(f"{base_url}/tasks/{task_id}", headers=headers, json={"priority": "low"})
    assert r.status_code == 200, r.text
    
    # 8. Get activity log
    r = httpx.get(f"{base_url}/tasks/{task_id}/activity", headers=headers)
    assert r.status_code == 200, r.text
    activities = r.json()
    print(f"Total activity logs: {len(activities)}")
    print("Latest activity:", activities[0]["field_changed"])
    
    print("Phase 4 Tests passed successfully.")

if __name__ == "__main__":
    test()
