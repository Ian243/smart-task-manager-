import requests
import json
import time

BASE_URL = "http://localhost:8000"

def login(email, password):
    res = requests.post(f"{BASE_URL}/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    res.raise_for_status()
    return res.json()["access_token"]

def main():
    try:
        # Login as manager
        token = login("g19asrithvatsal@gmail.com", "password123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Hit chatbot endpoint
        print("Sending message to Chatbot...")
        payload = {"message": "Can you create a high priority task for me to 'Review quarterly budget' due tomorrow?"}
        res = requests.post(f"{BASE_URL}/api/v1/ai/chat", headers=headers, json=payload)
        
        print(f"Status Code: {res.status_code}")
        try:
            print("Response:", json.dumps(res.json(), indent=2))
        except:
            print("Raw Response:", res.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
