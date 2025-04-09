import requests
import json
import datetime
from server_settings import OPENWEATHER_API_KEY

ZIP_CODE = 94022
COUNTRY_CODE = "US"
UNITS = "metric"

def geolocate():
    url = f"http://api.openweathermap.org/geo/1.0/zip?zip={ZIP_CODE},{COUNTRY_CODE}&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching weather geolocation: {str(e)}"}
    
    raw_geo = response.json()
    coords = {}
    coords["lat"] = raw_geo.get("lat")
    coords["lon"] = raw_geo.get("lon")
    return coords

def get_current_weather(coords):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords.get('lat')}&lon={coords.get('lon')}&appid={OPENWEATHER_API_KEY}&units={UNITS}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching weather data: {str(e)}"}
    
    raw_weather_data = response.json()
    current_weather = {}
    raw_date = raw_weather_data.get("dt")
    date = datetime.datetime.fromtimestamp(raw_date)
    formatted_date = date.strftime("%Y-%m-%d %I:%M %p")
    main_weather_data = raw_weather_data.get("main", {})
    weather_data = raw_weather_data.get("weather", [{}])[0]
    cloud_data = raw_weather_data.get("clouds", {})
    wind_data = raw_weather_data.get("wind", {})
    
    current_weather[formatted_date] = {
        "temp": main_weather_data.get("temp"),
        "feels_like": main_weather_data.get("feels_like"),
        "sky": weather_data.get("main"),
        "sky_description": weather_data.get("description"),
        "cloudyness": cloud_data.get("all"),
        "wind_speed": wind_data.get("speed")
    }
    
    return current_weather

def get_5day_forecast(coords):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={coords.get('lat')}&lon={coords.get('lon')}&appid={OPENWEATHER_API_KEY}&units={UNITS}"
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching weather data: {str(e)}"}
    
    raw_weather_data = response.json()
    weather_forecast_5_days = {}
    
    for data in raw_weather_data.get('list', []):
        raw_date = data.get("dt_txt")
        date = datetime.datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
        formatted_date = date.strftime("%Y-%m-%d %I:%M %p")
        main_weather_data = data.get("main", {})
        weather_data = data.get("weather", [{}])[0]
        cloud_data = data.get("clouds", {})
        wind_data = data.get("wind", {})
        
        weather_forecast_5_days[formatted_date] = {
            "temp": main_weather_data.get("temp"),
            "feels_like": main_weather_data.get("feels_like"),
            "sky": weather_data.get("main"),
            "sky_description": weather_data.get("description"),
            "cloudyness": cloud_data.get("all"),
            "wind_speed": wind_data.get("speed")
        }
        
    return weather_forecast_5_days
