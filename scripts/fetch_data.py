"""
STEP 1 — Data Extraction (Fetch Weather Data from API)
=======================================================
This script handles the 'Extract' part of our ETL pipeline.

What it does:
- Connects to the OpenWeather API
- Fetches real-time weather data for multiple cities
- Saves the raw API response as JSON

"""

import json
import os
import sys
from datetime import datetime

import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_URL, CITIES, DATA_DIR, OPENWEATHER_API_KEY, RAW_DATA_PATH
from scripts.logger_setup import get_logger

# Initialize logger for this module
logger = get_logger("fetch_data")


def fetch_weather_for_city(city: str) -> dict | None:
    """
    Fetches current weather data for a single city from OpenWeather API.

    Args:
        city: Name of the city to fetch weather for (e.g., "Mumbai")

    Returns:
        Dictionary containing weather data, or None if the request failed

    The API returns a lot of data — we grab everything and filter later
    during the Transform step. This follows the ETL principle of
    extracting raw data first, then cleaning it separately.
    """
    # Build the API request parameters
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",  # Get temperature in Celsius (not Kelvin)
    }

    try:
        logger.info(f"Fetching weather data for: {city}")
        response = requests.get(BASE_URL, params=params, timeout=10)

        # Check if the API returned an error (like 404 city not found)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Successfully fetched data for {city} — "
                     f"Temp: {data['main']['temp']}°C")
        return data

    except requests.exceptions.HTTPError as http_err:
        # This catches errors like 401 (bad API key) or 404 (city not found)
        logger.error(f"HTTP error for {city}: {http_err}")
        return None

    except requests.exceptions.ConnectionError:
        # No internet connection or API server is down
        logger.error(f"Connection error for {city}. Check your internet connection.")
        return None

    except requests.exceptions.Timeout:
        # API took too long to respond
        logger.error(f"Timeout error for {city}. API took too long to respond.")
        return None

    except requests.exceptions.RequestException as err:
        # Catch-all for any other request errors
        logger.error(f"Unexpected error fetching data for {city}: {err}")
        return None


def fetch_all_cities() -> list[dict]:
    """
    Fetches weather data for all cities defined in config.py

    Returns:
        List of dictionaries containing weather data for each city

    I'm collecting data for multiple cities to make the analysis
    more interesting — comparing weather across different locations
    is a common use case in data engineering.
    """
    all_weather_data = []

    logger.info(f"Starting data extraction for {len(CITIES)} cities...")

    for city in CITIES:
        weather_data = fetch_weather_for_city(city)
        if weather_data:
            # Add a timestamp so we know exactly when this data was fetched
            weather_data["fetch_timestamp"] = datetime.now().isoformat()
            all_weather_data.append(weather_data)

    logger.info(f"Successfully fetched data for {len(all_weather_data)}/{len(CITIES)} cities")
    return all_weather_data


def save_raw_data(data: list[dict]) -> bool:
    """
    Saves the raw API response data to a JSON file.

    Args:
        data: List of weather data dictionaries from the API

    Returns:
        True if save was successful, False otherwise

    Why save raw data?
    - It's a backup in case something goes wrong during transformation
    - We can re-run the transform step without hitting the API again
    - It's a data engineering best practice to keep raw data intact
    """
    try:
        # Create the data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)

        # Save with indent=4 for readability (easy to inspect manually)
        with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"Raw data saved to: {RAW_DATA_PATH}")
        logger.info(f"File size: {os.path.getsize(RAW_DATA_PATH) / 1024:.2f} KB")
        return True

    except IOError as e:
        logger.error(f"Failed to save raw data: {e}")
        return False

    except TypeError as e:
        # This happens if the data contains non-serializable objects
        logger.error(f"Data serialization error: {e}")
        return False


def generate_mock_weather_for_city(city: str) -> dict:
    """
    Generates realistic mock weather data for simulation when API key is missing.
    This allows the pipeline to be tested completely out-of-the-box!
    """
    import random
    
    city_bases = {
        "Mumbai": {"temp": 32.0, "humidity": 75, "weather": "Rain", "desc": "moderate rain", "country": "IN"},
        "Delhi": {"temp": 38.0, "humidity": 40, "weather": "Haze", "desc": "haze", "country": "IN"},
        "London": {"temp": 15.0, "humidity": 80, "weather": "Clouds", "desc": "broken clouds", "country": "GB"},
        "New York": {"temp": 22.0, "humidity": 60, "weather": "Clear", "desc": "clear sky", "country": "US"},
        "Tokyo": {"temp": 20.0, "humidity": 65, "weather": "Clouds", "desc": "scattered clouds", "country": "JP"},
        "Sydney": {"temp": 18.0, "humidity": 70, "weather": "Clear", "desc": "clear sky", "country": "AU"},
        "Dubai": {"temp": 40.0, "humidity": 30, "weather": "Clear", "desc": "clear sky", "country": "AE"},
        "Paris": {"temp": 17.0, "humidity": 72, "weather": "Mist", "desc": "mist", "country": "FR"},
        "Berlin": {"temp": 16.0, "humidity": 68, "weather": "Clouds", "desc": "few clouds", "country": "DE"},
        "Toronto": {"temp": 12.0, "humidity": 62, "weather": "Clear", "desc": "clear sky", "country": "CA"},
    }
    
    base = city_bases.get(city, {"temp": 20.0, "humidity": 60, "weather": "Clear", "desc": "clear sky", "country": "US"})
    
    temp = round(base["temp"] + random.uniform(-3.0, 3.0), 2)
    humidity = int(max(10, min(100, base["humidity"] + random.randint(-10, 10))))
    feels_like = round(temp + (0.1 if humidity > 70 else -0.1), 2)
    
    return {
        "name": city,
        "main": {
            "temp": temp,
            "feels_like": feels_like,
            "temp_min": round(temp - 2.0, 2),
            "temp_max": round(temp + 2.0, 2),
            "humidity": humidity,
            "pressure": random.randint(1005, 1025)
        },
        "weather": [{
            "main": base["weather"],
            "description": base["desc"]
        }],
        "wind": {
            "speed": round(random.uniform(1.5, 8.5), 2)
        },
        "visibility": random.randint(8000, 10000),
        "sys": {
            "country": base["country"]
        },
        "fetch_timestamp": datetime.now().isoformat()
    }


def run_extraction() -> bool:
    """
    Main function that orchestrates the entire extraction process.

    Returns:
        True if extraction was successful, False otherwise

    This is the function that main.py calls to kick off Step 1 of the pipeline.
    """
    logger.info("=" * 60)
    logger.info("STEP 1: DATA EXTRACTION — Starting...")
    logger.info("=" * 60)

    # Validate API key before making requests
    use_mock = False
    if OPENWEATHER_API_KEY == "YOUR_API_KEY_HERE":
        logger.warning(
            "API key not configured! Entering SIMULATION MODE. "
            "Generating mock weather data for pipeline execution. "
            "Configure OPENWEATHER_API_KEY in config.py for real weather data."
        )
        use_mock = True

    # Fetch/Generate weather data for all configured cities
    weather_data = []
    if use_mock:
        logger.info(f"Generating mock weather data for {len(CITIES)} cities...")
        for city in CITIES:
            weather_data.append(generate_mock_weather_for_city(city))
    else:
        weather_data = fetch_all_cities()

    if not weather_data:
        logger.error("No data was fetched/generated. Extraction failed.")
        return False

    # Save the raw data to JSON
    success = save_raw_data(weather_data)

    if success:
        logger.info("STEP 1: DATA EXTRACTION — Completed successfully! ✓")
    else:
        logger.error("STEP 1: DATA EXTRACTION — Failed!")

    return success


# This allows running the script standalone for testing
if __name__ == "__main__":
    run_extraction()
