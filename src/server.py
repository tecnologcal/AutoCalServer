from flask import Flask, jsonify
from process_google_tasks import get_google_classroom_data
from process_canvas_tasks import get_canvas_data

app = Flask(__name__)

@app.route("/")
def get_task_payload():
    
    google_tasks = get_google_classroom_data()
    canvas_tasks = get_canvas_data()

    
    task_payload = {}
    task_payload.update(google_tasks)
    task_payload.update(canvas_tasks)

    
    return jsonify(task_payload)

if __name__ == "__main__":
    app.run()