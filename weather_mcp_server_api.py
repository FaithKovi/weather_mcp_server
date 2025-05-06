import os
import json
import logging
from dotenv import load_dotenv
import aiohttp
import asyncio
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get API key from environment variables
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    logger.error("OpenWeather API key not found. Please set it in the .env file.")
    exit(1)

# FastAPI app
app = FastAPI()

# Pydantic model to validate incoming request body
class LocationRequest(BaseModel):
    location: str

# Utility function to fetch weather data
async def get_weather_data(location):
    """Fetch current weather data for a location using OpenWeatherMap API"""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                'q': location,
                'appid': OPENWEATHER_API_KEY,
                'units': 'metric'
            }
            async with session.get('https://api.openweathermap.org/data/2.5/weather', params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error fetching weather: {error_text}")
                    raise Exception(f"Unable to fetch weather for {location}: {response.status}")
                
                return await response.json()
    except Exception as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        raise Exception(f"Unable to fetch weather for {location}: {str(e)}")

# Utility function to fetch weather alerts
async def get_weather_alerts(location):
    """Fetch weather alerts for a location using OpenWeatherMap API"""
    try:
        # First get coordinates for the location
        weather_data = await get_weather_data(location)
        lat, lon = weather_data['coord']['lat'], weather_data['coord']['lon']
        
        # Then use these coordinates to fetch alerts
        async with aiohttp.ClientSession() as session:
            params = {
                'lat': lat,
                'lon': lon,
                'exclude': 'current,minutely,hourly,daily',
                'appid': OPENWEATHER_API_KEY
            }
            async with session.get('https://api.openweathermap.org/data/2.5/onecall', params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error fetching alerts: {error_text}")
                    raise Exception(f"Unable to fetch alerts for {location}: {response.status}")
                
                data = await response.json()
                return data.get('alerts', [])
    except Exception as e:
        logger.error(f"Error fetching weather alerts: {str(e)}")
        raise Exception(f"Unable to fetch alerts for {location}: {str(e)}")

# Route for current weather
@app.post("/get_current_weather")
async def get_current_weather(request: LocationRequest):
    """API route handler for current weather"""
    try:
        location = request.location
        data = await get_weather_data(location)
        
        return {
            'location': f"{data['name']}, {data['sys']['country']}",
            'temperature': f"{data['main']['temp']}°C",
            'feels_like': f"{data['main']['feels_like']}°C",
            'humidity': f"{data['main']['humidity']}%", 
            'wind_speed': f"{data['wind']['speed']} m/s",
            'conditions': data['weather'][0]['description'],
            'updated': datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Weather tool error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# Route for weather alerts
@app.post("/get_weather_alerts")
async def get_weather_alerts_api(request: LocationRequest):
    """API route handler for weather alerts"""
    try:
        location = request.location
        alerts = await get_weather_alerts(location)
        
        if not alerts:
            return {
                'location': location,
                'status': 'No active weather alerts for this location',
                'alerts': []
            }
        
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append({
                'event': alert['event'],
                'description': alert['description'],
                'start': datetime.fromtimestamp(alert['start']).strftime('%Y-%m-%d %H:%M:%S'),
                'end': datetime.fromtimestamp(alert['end']).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            'location': location,
            'status': f"{len(alerts)} active weather alert(s) found",
            'alerts': formatted_alerts
        }
    except Exception as e:
        logger.error(f"Weather alerts tool error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
