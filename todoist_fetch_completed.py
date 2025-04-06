import requests
import pandas as pd

# Replace with your Todoist API Token
API_TOKEN = "6e36c8b1cda40ab13abd31de805358cddc4e445a"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# Fetch All Active Tasks
tasks_url = "https://api.todoist.com/rest/v2/tasks"
tasks_response = requests.get(tasks_url, headers=HEADERS)
tasks = tasks_response.json()

# Convert to DataFrame
tasks_df = pd.DataFrame(tasks)

# Fetch Completed Tasks Since January 1, 2024
completed_tasks = []
next_cursor = None  # For pagination

while True:
    completed_url = "https://api.todoist.com/sync/v9/completed/get_all"
    params = {
        "since": "2024-01-01T00:00:00Z",  # Fetch all tasks from January 1, 2024
        "until": "2024-12-31T23:59:59Z",  # Optional: Limit to 2024
        "limit": 200,  # Fetch in batches of 200
        "cursor": next_cursor
    }
    
    completed_response = requests.get(completed_url, headers=HEADERS, params=params)
    data = completed_response.json()
    
    completed_tasks.extend(data.get("items", []))  # Add to list
    
    next_cursor = data.get("next_cursor")  # Check if there's more data
    if not next_cursor:  # Stop if no more pages
        break

# Convert completed tasks to DataFrame
completed_df = pd.DataFrame(completed_tasks)

# Merge DataFrames
tasks_df["completed"] = tasks_df["id"].isin(completed_df["task_id"])

# Save to CSV
completed_df.to_csv("todoist_completed_tasks.csv", index=False)

print("Todoist completed tasks data successfully exported with LATEST data! YAY")
