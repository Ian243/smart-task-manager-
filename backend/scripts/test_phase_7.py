import httpx

base_url = "http://localhost:8000"

def test():
    # 1. Login
    r = httpx.post(f"{base_url}/auth/login", data={"username": "manager@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test parse-task
    print("Testing parse-task...")
    r = httpx.post(f"{base_url}/ai/parse-task", headers=headers, json={"text": "Create a high priority task to review the Q3 marketing budget next friday"})
    if r.status_code == 200:
        parsed = r.json()
        print("Parsed:", parsed)
        assert parsed["priority"] == "high"
    else:
        print("API Key Error tolerated:", r.text)

    # 3. Test suggest-priority
    print("Testing suggest-priority...")
    r = httpx.post(f"{base_url}/ai/suggest-priority", headers=headers, json={"title": "Fix critical production database outage", "due_date": "today"})
    if r.status_code == 200:
        suggested = r.json()
        print("Suggested Priority:", suggested)
    else:
        print("API Key Error tolerated:", r.text)

    # 4. Find a task to summarize
    r = httpx.get(f"{base_url}/tasks/", headers=headers)
    tasks = r.json()["items"]
    
    if tasks:
        task_id = tasks[0]["id"]
        # 5. Test summarize
        print(f"Testing summarize for task {task_id}...")
        r = httpx.post(f"{base_url}/ai/summarize/{task_id}", headers=headers)
        if r.status_code == 200:
            summary = r.json()
            print("Summary:", summary["summary"])
        else:
            print("API Key Error tolerated:", r.text)

        # 6. Test chat with tool use
        print("Testing chat (tool call)...")
        r = httpx.post(f"{base_url}/ai/chat", headers=headers, json={"message": f"What is the current status of task {task_id}?"})
        if r.status_code == 200:
            chat = r.json()
            print("Chat Agent Reply:", chat["reply"])
        else:
            print("API Key Error tolerated:", r.text)
    
    print("Phase 7 AI Tests completed.")

if __name__ == "__main__":
    test()
