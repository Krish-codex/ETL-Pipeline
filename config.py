"""
Configuration file for the ETL Pipeline project.
Stores all API keys, database credentials, and project settings in one place.

"""

import os

# ========================
# OpenWeather API Settings
# ========================
# Sign up at https://openweathermap.org/api to get your free API key
# The free tier gives us 60 calls/minute which is more than enough

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# List of cities to fetch weather data for
# I picked a mix of cities across different climates to make the analysis interesting
CITIES = [
    "Mumbai",
    "Delhi",
    "London",
    "New York",
    "Tokyo",
    "Sydney",
    "Dubai",
    "Paris",
    "Berlin",
    "Toronto",
]

# ========================
# MySQL Database Settings
# ========================
# Make sure MySQL server is running before executing the pipeline
# Update these credentials to match your local MySQL setup

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",  # Change this to your MySQL root password
    "database": "weather_pipeline",
}

# ========================
# File Paths
# ========================
# Using os.path for cross-platform compatibility (works on Windows, Mac, Linux)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SQL_DIR = os.path.join(BASE_DIR, "sql")

RAW_DATA_PATH = os.path.join(DATA_DIR, "raw_weather_data.json")
CLEANED_DATA_PATH = os.path.join(DATA_DIR, "cleaned_weather_data.csv")
ANALYSIS_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "analysis_results.txt")
SQLITE_DB_PATH = os.path.join(DATA_DIR, "weather_pipeline.db")

# ========================
# Logging Settings
# ========================
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")
