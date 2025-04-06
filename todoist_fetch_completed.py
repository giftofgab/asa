import requests
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# ========== STEP 1: Todoist API ==========
API_TOKEN = "6e36c8b1cda40ab13abd31de805358cddc4e445a"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# Fetch Completed Tasks From Jan 1, 2025 to Today
start_date = "2025-01-01T00:00:00Z"
end_date = datetime.utcnow().isoformat("T") + "Z"

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
    completed_tasks.extend(batch)
    fetch_count += len(batch)
    print(f"Fetched {len(batch)} tasks (Total so far: {fetch_count})")

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
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the correct sheet and tab
spreadsheet = client.open("ASA log")
worksheet = spreadsheet.worksheet("todoist_completed_tasks")

# Clear previous content
worksheet.clear()

# Clean the DataFrame
clean_df = completed_df.fillna("").astype(str)

# Upload DataFrame to Google Sheets
if not clean_df.empty:
    worksheet.update(
        [clean_df.columns.values.tolist()] + clean_df.values.tolist()
    )
    print("✅ Google Sheet updated successfully.")
else:
    print("⚠️ No completed tasks found. Sheet not updated.")
