import httpx
import sys

base_url = "http://localhost:8000"

def test():
    # 1. Login as Manager
    r = httpx.post(f"{base_url}/auth/login", data={"username": "manager@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    manager_token = r.json()["access_token"]
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    # 2. Get Manager Dashboard (Global)
    r = httpx.get(f"{base_url}/dashboard/summary", headers=manager_headers)
    assert r.status_code == 200, r.text
    manager_stats = r.json()
    print("Manager Stats:", manager_stats)

    # 3. Login as Member
    r = httpx.post(f"{base_url}/auth/login", data={"username": "member1@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    member_token = r.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    # 4. Get Member Dashboard (Scoped)
    r = httpx.get(f"{base_url}/dashboard/summary", headers=member_headers)
    assert r.status_code == 200, r.text
    member_stats = r.json()
    print("Member Stats:", member_stats)

    # Note: Manager should generally see >= total tasks than member
    assert manager_stats["total_tasks"] >= member_stats["total_tasks"]

    print("Phase 5 Tests passed successfully.")

if __name__ == "__main__":
    test()
