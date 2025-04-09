import requests
from datetime import datetime
import pytz
import json
import html
from bs4 import BeautifulSoup
from server_settings import CANVAS_API_KEY, CURRENT_CANVAS_ENROLLMENT_ID

def clean_html(html_content):
    if html_content is None:
        return None
    decoded_content = html.unescape(html_content)
    
    soup = BeautifulSoup(html_content, "html.parser")
    processed_text = soup.get_text()
    cleaned_content = processed_text.replace("\n", " ").replace("\xa0", " ").strip()

    return cleaned_content

def get_canvas_data():
    base_url = "https://mvla.instructure.com"
    headers = {"Authorization": f"Bearer {CANVAS_API_KEY}"}

    courses_url = f"{base_url}/api/v1/users/self/courses"
    try:
        response = requests.get(courses_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching Canvas courses: {str(e)}"}

    raw_courses = response.json()
    processed_courses = {}

    for course in raw_courses:
        if "name" in course and "enrollment_term_id" in course:
            enrollment_id = course["enrollment_term_id"]
            if enrollment_id == CURRENT_CANVAS_ENROLLMENT_ID:
                course_name = course.get("name")
                course_id = course.get("id")
                processed_courses[course_name] = course_id

    TIMEZONE = pytz.timezone('US/Pacific')
    today = datetime.today().astimezone(TIMEZONE)
    all_info = {}

    for course_name, course_id in processed_courses.items():
        url = f"{base_url}/api/v1/courses/{course_id}/assignments?per_page=100"
        course_assignment_list = {}

        while url:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()

                raw_assignments = response.json()
                for assignment in raw_assignments:
                    due_date = assignment.get("due_at")
                    description = assignment.get("description", "No description available")  # Default description if none exists
                    
                    description = clean_html(description)
                    if description is None:
                        description = "No description"
                    if not due_date:
                        continue

                    due_date_utc = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%SZ")
                    due_date_utc = pytz.utc.localize(due_date_utc)
                    due_date_local = due_date_utc.astimezone(TIMEZONE)

                    if due_date_local < today:
                        continue
                    
                    formatted_due_date = due_date_local.strftime("%Y-%m-%d %H:%M")

                    assignment_name = assignment.get("name")
                    if assignment_name:
                        course_assignment_list[assignment_name] = {
                            "due_date": formatted_due_date,
                            "description": description
                        }
            except requests.exceptions.RequestException as e:
                return {"error": f"Error fetching assignments for {course_name}: {str(e)}"}

            next_url = None
            if "link" in response.headers:
                links = response.headers["link"].split(",")
                for link in links:
                    if 'rel="next"' in link:
                        next_url = link[link.find("<") + 1 : link.find(">")]
                        break

            url = next_url

        all_info[course_name] = course_assignment_list
    
    #print("canvas info")
    #print(json.dumps(all_info, indent=2))
    return all_info