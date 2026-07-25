import time
import requests

API_URL = "http://127.0.0.1:8000"

def wait_for_api():
    print("Waiting for API...")
    for _ in range(30):
        try:
            r = requests.get(f"{API_URL}/health")
            if r.status_code == 200:
                print("API is up!")
                return
        except:
            pass
        time.sleep(1)
    raise Exception("API did not start")

def submit_goal():
    print("Submitting goal...")
    r = requests.post(
        f"{API_URL}/ceo/goal",
        json={
            "id": "goal-flask-blog-1",
            "description": "Create a Flask blog application in the workspace."
        }
    )
    r.raise_for_status()
    print("Goal submitted:", r.json())
    return r.json()["session_id"]

def poll_approvals():
    print("Polling for approvals...")
    # Poll for 2 minutes
    end_time = time.time() + 300
    while time.time() < end_time:
        try:
            r = requests.get(f"{API_URL}/approvals")
            r.raise_for_status()
            pending = r.json().get("pending_approvals", [])
            for approval in pending:
                print(f"\n[!] APPROVAL REQUIRED: {approval['context']}")
                print(f"    Approving {approval['id']} automatically...")
                requests.post(
                    f"{API_URL}/approvals/{approval['id']}",
                    json={"approved": True, "feedback": "Approved by Founder script."}
                )
                print("    Approved.")
        except Exception as e:
            print("Error polling approvals:", e)
        time.sleep(3)
    print("Finished polling.")

if __name__ == "__main__":
    wait_for_api()
    submit_goal()
    poll_approvals()
