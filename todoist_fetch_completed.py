import os
import requests
import pandas as pd
from datetime import datetime, timezone
import json
import time
import base64

# ========== STEP 1: Todoist API ==========
API_TOKEN = os.getenv("API_TOKEN")  # Fetch API token from environment variable
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# GitHub credentials
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "username/repository"  # Replace with your GitHub repo (e.g., "user/repo")
GITHUB_BRANCH = "main"  # Replace with your branch name
GITHUB_FILE_PATH = "data/todoist_completed_tasks.csv"  # Path within the repo

# Fetch Completed Tasks From Jan 1, 2025 to Today
start_date = "2025-01-01T00:00:00Z"
end_date = datetime.now(timezone.utc).isoformat("T")

completed_tasks = []
next_cursor = None
fetch_count = 0

while True:
    completed_url = "https://api.todoist.com/sync/v9/completed/get_all"
    params = {
        "since": start_date,
        "until": end_date,
        "limit": 200
    }
    if next_cursor:
        params["cursor"] = next_cursor

    completed_response = requests.get(completed_url, headers=HEADERS, params=params)
    data = completed_response.json()

    batch = data.get("items", [])
    fetch_count += len(batch)
    print(f"Fetched {len(batch)} tasks (Total so far: {fetch_count})")

    # Extract the original task ID and other useful data
    for task in batch:
        task_id = task.get("task_id", "N/A")  # Original task ID
        content = task.get("content", "N/A")
        project_id = task.get("project_id", "N/A")
        completed_date = task.get("completed_date", "N/A")
        completed_tasks.append({
            "Content": content,
            "Project ID": project_id,
            "Completed Date": completed_date,
            "Original Task ID": task_id  # Add original ID here
        })

    next_cursor = data.get("next_cursor")
    if not next_cursor:
        print("✅ All completed tasks fetched.")
        break

    time.sleep(0.2)  # Small delay for rate limiting

# Create DataFrame
completed_df = pd.DataFrame(completed_tasks)

# ========== STEP 2: Save to CSV Locally ==========
try:
    download_path = os.path.expanduser("~/Downloads/todoist_completed_tasks.csv")
    completed_df.to_csv(download_path, index=False)
    print(f"✅ CSV saved to: {download_path}")
except Exception as e:
    print(f"❌ Failed to save CSV: {e}")

# ========== STEP 3: Upload to GitHub ==========
def upload_to_github(local_file, repo, branch, remote_path):
    try:
        with open(local_file, "rb") as file:
            content = base64.b64encode(file.read()).decode()

        url = f"https://api.github.com/repos/{repo}/contents/{remote_path}"
        response = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
        sha = response.json().get("sha")

        payload = {
            "message": "Update completed tasks CSV",
            "content": content,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha

        response = requests.put(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}, data=json.dumps(payload))

        if response.status_code in [200, 201]:
            print("✅ File successfully uploaded to GitHub!")
        else:
            print(f"❌ GitHub upload failed: {response.json().get('message')}")
    except Exception as e:
        print(f"❌ Error uploading to GitHub: {e}")

# Upload to GitHub
upload_to_github(download_path, GITHUB_REPO, GITHUB_BRANCH, GITHUB_FILE_PATH)
