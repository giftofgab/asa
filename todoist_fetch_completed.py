import os
import requests
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone
import json
import time

# ========== STEP 1: Todoist API ==========
API_TOKEN = os.getenv("API_TOKEN")  # Fetch API token from environment variable
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

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

completed_df = pd.DataFrame(completed_tasks)

# ========== STEP 2: Update Google Sheet ==========
# Google Sheets Auth
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load the Google credentials from the environment variable
try:
    google_credentials = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_credentials, scope)
    client = gspread.authorize(creds)
    print("✅ Google Sheets authentication successful.")
except Exception as e:
    print(f"❌ Failed to authenticate with Google Sheets: {e}")
    exit(1)

# Open the correct sheet and tab
try:
    spreadsheet = client.open("ASA log")
    worksheet = spreadsheet.worksheet("todoist_completed_tasks")
    print("✅ Successfully accessed Google Sheet.")
except Exception as e:
    print(f"❌ Failed to open the spreadsheet or worksheet: {e}")
    exit(1)

# Clear previous content
try:
    worksheet.clear()
    print("✅ Worksheet cleared successfully.")
except Exception as e:
    print(f"❌ Failed to clear the worksheet: {e}")
    exit(1)

# Clean the DataFrame
clean_df = completed_df.fillna("").astype(str)

# Upload DataFrame to Google Sheets
try:
    if not clean_df.empty:
        worksheet.update([clean_df.columns.values.tolist()] + clean_df.values.tolist())
        print("✅ Google Sheet updated successfully.")
    else:
        print("⚠️ No completed tasks found. Sheet not updated.")
except Exception as e:
    print(f"❌ Failed to update Google Sheet: {e}")
    exit(1)
