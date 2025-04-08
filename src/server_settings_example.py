import os

# Defines paths, scopes, and other things for google classroom api fetch
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "secrets", "credentials.json")
TOKEN_FOLDER = os.path.join(BASE_DIR, "secrets")
TOKEN_PATH = os.path.join(TOKEN_FOLDER, "token.json")

# Canvas API key and course ID
CANVAS_API_KEY = "YOUR API KEY"
CURRENT_CANVAS_ENROLLMENT_ID = "YOUR CANVAS COURSE ENROLLMENT ID FOR THE YEAR"

# Openweather API
OPENWEATHER_API_KEY= "YOUR API KEY"

