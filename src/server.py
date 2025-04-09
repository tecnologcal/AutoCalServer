from flask import Flask, jsonify
from sync_todoist import get_todoist_data, push_task_list_to_todoist
from request_weather_data import get_5day_forecast, get_current_weather, geolocate
app = Flask(__name__)

@app.route("/tasks")
def get_task_payload():
    
    push_task_list_to_todoist()
    
    
    return jsonify(get_todoist_data())

@app.route("/weather")
def get_weather_payload():
    coords = geolocate()
    weather_payload = get_current_weather(coords)
    weather_payload.update(get_5day_forecast(coords))
    
    return jsonify(weather_payload)
    
    
if __name__ == "__main__":
    app.run()