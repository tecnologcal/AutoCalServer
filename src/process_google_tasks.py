from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import datetime
import json
import html
from bs4 import BeautifulSoup
from server_settings import SCOPES, CREDENTIALS_PATH, TOKEN_PATH, TOKEN_FOLDER

def clean_html(html_content):
    if html_content is None:
        return None
    decoded_content = html.unescape(html_content)
    soup = BeautifulSoup(decoded_content, "html.parser")
    processed_text = soup.get_text()
    cleaned_content = processed_text.replace("\n", " ").replace("\xa0", " ").strip()
    return cleaned_content

def authenticate():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save credentials for the next run
        if not os.path.exists(TOKEN_FOLDER):
            os.makedirs(TOKEN_FOLDER)
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
    return creds

def get_google_classroom_data():
    creds = authenticate()
    service = build("classroom", "v1", credentials=creds)
    
    # Get courses
    try:
        response = service.courses().list().execute()
        raw_courses = response.get("courses", [])
    except Exception as e:
        return {"error": f"Error fetching Google Classroom data: {str(e)}"}

    processed_courses = {}

    for course in raw_courses:
        if course.get("courseState") == "ACTIVE":
            course_name = course.get("name")
            course_id = course.get("id")
            processed_courses[course_name] = course_id
    today = datetime.datetime.today()
    all_info = {}

    # Get assignments for each course
    for course_name, course_id in processed_courses.items():
        course_assignment_list = {}
        try:
            response = service.courses().courseWork().list(courseId=course_id).execute()
            course_assignments = response.get("courseWork", [])

            for assignment in course_assignments:
                due_dates = assignment.get("dueDate")
                due_times = assignment.get("dueTime", {"hours": 0, "minutes": 0})
                due_hour = due_times.get("hours", 0)
                due_minute = due_times.get("minutes", 0)

                if not due_dates:
                    continue

                due_string = f"{due_dates.get('year')}-{due_dates.get('month')}-{due_dates.get('day')} {due_hour}:{due_minute}"
                due_datetime = datetime.datetime.strptime(due_string, "%Y-%m-%d %H:%M")

                if due_datetime <= today:
                    continue

                assignment_name = assignment.get("title")
                description = assignment.get("description", "No description available")  
                description = clean_html(description)  
                if description is None:
                    description = "No description"
                course_assignment_list[assignment_name] = {
                    "due_date": due_datetime.strftime("%Y-%m-%d %I:%M"),
                    "description": description
                }
        except Exception as e:
            return {"error": f"Error fetching assignments for {course_name}: {str(e)}"}

        all_info[course_name] = course_assignment_list

    #print("google info")
    #print(json.dumps(all_info, indent=2))
    return all_info

