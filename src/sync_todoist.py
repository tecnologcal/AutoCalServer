import requests
import json
import pytz
from datetime import datetime
from server_settings import TODOIST_API_KEY
from process_google_tasks import get_google_classroom_data
from process_canvas_tasks import get_canvas_data
from pytz import timezone


TODOIST_API_URL = "https://api.todoist.com/rest/v2/tasks"
HEADERS = {
    "Authorization": f"Bearer {TODOIST_API_KEY}",
    "Content-Type": "application/json"
}
TIMEZONE = pytz.timezone('America/Los_Angeles')

def get_todoist_data():
    try:
        response = requests.get(TODOIST_API_URL, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching Todoist tasks: {str(e)}"}

    raw_tasks = response.json()
    all_info = {}

    for task in raw_tasks:
        task_name = task.get("content")
        due_info = task.get("due")
        labels = task.get("labels", [])
        description = task.get("description", "No description")

        if not task_name or not labels:
            continue

        if due_info:
            due = due_info.get("datetime") or due_info.get("date")  
            if not due:
                continue
        else:
            continue

        try:
            if ":" in due:
                due_datetime_utc = datetime.strptime(due, "%Y-%m-%dT%H:%M:%S%z")
                due_datetime_local = due_datetime_utc.astimezone(TIMEZONE)
                due_datetime_str = due_datetime_local.strftime("%Y-%m-%d %H:%M")
            else:
                due_datetime_utc = datetime.strptime(due, "%Y-%m-%d")
                due_datetime_str = f"{due_datetime_utc} 11:59"
        except Exception as e:
            print(f"Failed to parse due date for task '{task_name}': {e}")
            continue

        course_name = labels[0]  
        
        if course_name not in all_info:
            all_info[course_name] = {}

        # Store task data for the course
        all_info[course_name][task_name] = {
            "due_date": due_datetime_str,
            "description": description
        }

    return all_info

def make_signature(task):
    return (task["content"].strip().lower(), task["due_string"].strip())

def compare_tasks(existing_tasks, current_tasks):
    """Compare existing Todoist tasks with current Canvas tasks."""
    existing_signatures = {
        make_signature(task): task
        for task in existing_tasks
    }

    new_or_changed_tasks = []

    for task in current_tasks:
        sig = make_signature(task)
        if sig in existing_signatures:
            print(
                f"3rdphase: Task exists\n"
                f"  Existing content: {existing_signatures[sig]['content']}\n"
                f"  Current content:  {task['content']}\n"
                f"  Existing due:     {existing_signatures[sig]['due_string']}\n"
                f"  Current due:      {task['due_string']}\n"
            )
        else:
            print(
                f"New or changed task detected:\n"
                f"  Content: {task['content']}\n"
                f"  Due:     {task['due_string']}\n"
            )
            new_or_changed_tasks.append(task)

    return new_or_changed_tasks

def get_label_name(course_name):
    labels_url = "https://api.todoist.com/rest/v2/labels"
    label_resp = requests.get(labels_url, headers=HEADERS)
    label_resp.raise_for_status()
    labels = label_resp.json()

    for label in labels:
        if label["name"] == course_name:
            return label["name"]

    create_label = requests.post(labels_url, headers=HEADERS, json={"name": course_name})
    if create_label.status_code == 200:
        return create_label.json()["name"]
    else:
        print(f"Failed to create label for course '{course_name}': {create_label.status_code}")
        return None

def push_task_list_to_todoist():
    google_tasks = get_google_classroom_data()
    canvas_tasks = get_canvas_data()

    all_tasks = {}
    all_tasks.update(google_tasks)
    all_tasks.update(canvas_tasks)

    existing_tasks = get_todoist_data()

    for course, assignments in all_tasks.items():
        label_name = get_label_name(course)
        if not label_name:
            continue

        for assignment_name, due_info in assignments.items():
            task_exists = False
            description = due_info.get("description", "No description")
            due_date = due_info.get("due_date")

            if course in existing_tasks:
                for existing_assignment, existing_task_info in existing_tasks[course].items():
                    existing_due_date = existing_task_info.get("due_date")

                    if not existing_due_date:
                        continue

                    try:
                        existing_due_date_obj = datetime.strptime(existing_due_date, "%Y-%m-%d %H:%M")
                        current_due_date_obj = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
                    except Exception as e:
                        continue

                    if existing_assignment == assignment_name and existing_due_date_obj == current_due_date_obj:
                        task_exists = True
                        break

            if not task_exists:

                due_datetime = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
                localized_due_date = TIMEZONE.localize(due_datetime)
                due_datetime_with_tz = localized_due_date.isoformat()

                payload = {
                    "content": assignment_name,
                    "description": description, 
                    "due_datetime": due_datetime_with_tz,
                    "labels": [label_name]
                }

                response = requests.post(TODOIST_API_URL, headers=HEADERS, json=payload)
                if response.status_code not in (200, 204):
                    print(f"Failed to add task '{assignment_name}' for course '{label_name}': {response.status_code} - {response.text}")
                else:
                    print(f"Added task '{assignment_name}' for course '{label_name}'")


