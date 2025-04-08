import requests
import json
from datetime import datetime
from server_settings import CANVAS_API_KEY, CURRENT_CANVAS_ENROLLMENT_ID

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

    today = datetime.today()
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
                    if not due_date:
                        continue

                    due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%SZ")
                    if due_date < today:
                        continue

                    assignment_name = assignment.get("name")
                    if assignment_name:
                        course_assignment_list[assignment_name] = due_date.strftime("%Y-%m-%d %H:%M")
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

    return all_info
