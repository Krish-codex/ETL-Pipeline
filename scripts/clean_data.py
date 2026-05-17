"""
STEP 2 — Data Transformation (Clean & Structure the Data)
==========================================================
This script handles the 'Transform' part of our ETL pipeline.

What it does:
- Reads the raw JSON data saved by fetch_data.py
- Extracts only the fields we need (city, temp, humidity, etc.)
- Handles missing or malformed data gracefully
- Converts everything into a clean pandas DataFrame
- Saves the result as a CSV file

"""

import json
import os
import sys
from datetime import datetime

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CLEANED_DATA_PATH, DATA_DIR, RAW_DATA_PATH
from scripts.logger_setup import get_logger

# Initialize logger for this module
logger = get_logger("clean_data")


def load_raw_data() -> list[dict] | None:
    """
    Loads raw weather data from the JSON file.

    Returns:
        List of raw weather data dictionaries, or None if loading failed

    This reads the file that was created during the extraction step.
    If the file doesn't exist, it means Step 1 hasn't been run yet.
    """
    try:
        if not os.path.exists(RAW_DATA_PATH):
            logger.error(
                f"Raw data file not found at: {RAW_DATA_PATH}. "
                f"Please run the extraction step first (fetch_data.py)"
            )
            return None

        with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data)} records from raw data file")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file: {e}")
        return None

    except IOError as e:
        logger.error(f"Failed to read raw data file: {e}")
        return None


def extract_weather_fields(raw_record: dict) -> dict | None:
    """
    Extracts relevant fields from a single raw API response record.

    Args:
        raw_record: A single weather data dictionary from the API

    Returns:
        Dictionary with cleaned fields, or None if extraction failed

    The API returns a LOT of nested data — we only need a few key fields.
    This function digs into the nested structure and pulls out what we need.

    Example raw structure from API:
    {
        "name": "Mumbai",
        "main": {"temp": 32.5, "humidity": 78, ...},
        "weather": [{"main": "Clouds", "description": "scattered clouds"}],
        ...
    }
    """
    try:
        cleaned = {
            "city": raw_record.get("name", "Unknown"),
            "temperature": raw_record.get("main", {}).get("temp"),
            "feels_like": raw_record.get("main", {}).get("feels_like"),
            "temp_min": raw_record.get("main", {}).get("temp_min"),
            "temp_max": raw_record.get("main", {}).get("temp_max"),
            "humidity": raw_record.get("main", {}).get("humidity"),
            "pressure": raw_record.get("main", {}).get("pressure"),
            "weather_condition": (
                raw_record.get("weather", [{}])[0].get("main", "Unknown")
            ),
            "weather_description": (
                raw_record.get("weather", [{}])[0].get("description", "Unknown")
            ),
            "wind_speed": raw_record.get("wind", {}).get("speed"),
            "visibility": raw_record.get("visibility"),
            "country": raw_record.get("sys", {}).get("country", "Unknown"),
            "timestamp": raw_record.get(
                "fetch_timestamp", datetime.now().isoformat()
            ),
        }
        return cleaned

    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Failed to extract fields from record: {e}")
        return None


def clean_and_transform(raw_data: list[dict]) -> pd.DataFrame | None:
    """
    Cleans and transforms raw weather data into a structured DataFrame.

    Args:
        raw_data: List of raw weather data dictionaries

    Returns:
        Cleaned pandas DataFrame, or None if transformation failed

    This is where the real 'Transform' magic happens:
    1. Extract relevant fields from each record
    2. Create a DataFrame
    3. Handle missing values
    4. Convert data types
    5. Add derived columns
    """
    logger.info("Starting data transformation...")

    # Step 1: Extract fields from each record
    cleaned_records = []
    for i, record in enumerate(raw_data):
        cleaned = extract_weather_fields(record)
        if cleaned:
            cleaned_records.append(cleaned)
        else:
            logger.warning(f"Skipped record {i + 1} due to extraction failure")

    if not cleaned_records:
        logger.error("No records survived the cleaning process!")
        return None

    # Step 2: Create a pandas DataFrame
    df = pd.DataFrame(cleaned_records)
    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")

    # Step 3: Handle missing values
    # For numeric columns, fill missing values with the column median
    # Median is better than mean because it's less affected by outliers
    numeric_cols = ["temperature", "feels_like", "humidity", "pressure", "wind_speed"]
    for col in numeric_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                median_value = df[col].median()
                df[col] = df[col].fillna(median_value)
                logger.info(f"Filled {missing_count} missing values in '{col}' with median: {median_value}")

    # For text columns, fill missing values with 'Unknown'
    text_cols = ["city", "weather_condition", "weather_description", "country"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # Step 4: Convert data types for consistency
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Step 5: Add derived/calculated columns
    # Temperature category — useful for grouping in analysis later
    df["temp_category"] = pd.cut(
        df["temperature"],
        bins=[-float("inf"), 0, 15, 25, 35, float("inf")],
        labels=["Freezing", "Cold", "Mild", "Warm", "Hot"],
    )

    # Round numeric columns to 2 decimal places for cleaner output
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].round(2)

    # Step 6: Remove duplicate entries (same city fetched twice by accident)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["city"], keep="last")
    after_dedup = len(df)
    if before_dedup != after_dedup:
        logger.info(f"Removed {before_dedup - after_dedup} duplicate records")

    logger.info(f"Transformation complete. Final DataFrame: {df.shape}")
    return df


def save_cleaned_data(df: pd.DataFrame) -> bool:
    """
    Saves the cleaned DataFrame to a CSV file.

    Args:
        df: Cleaned pandas DataFrame

    Returns:
        True if save was successful, False otherwise

    CSV format is chosen because:
    - It's universally readable (Excel, databases, other tools)
    - It's easy to inspect manually
    - It's lightweight and fast to read/write
    """
    try:
        # Create the data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)

        # index=False because we don't need pandas' row numbers in the CSV
        df.to_csv(CLEANED_DATA_PATH, index=False, encoding="utf-8")

        logger.info(f"Cleaned data saved to: {CLEANED_DATA_PATH}")
        logger.info(f"File size: {os.path.getsize(CLEANED_DATA_PATH) / 1024:.2f} KB")
        logger.info(f"Records saved: {len(df)}")
        return True

    except IOError as e:
        logger.error(f"Failed to save cleaned data: {e}")
        return False


def run_transformation() -> bool:
    """
    Main function that orchestrates the entire transformation process.

    Returns:
        True if transformation was successful, False otherwise

    This is the function that main.py calls to kick off Step 2 of the pipeline.
    """
    logger.info("=" * 60)
    logger.info("STEP 2: DATA TRANSFORMATION — Starting...")
    logger.info("=" * 60)

    # Load raw data from JSON
    raw_data = load_raw_data()
    if raw_data is None:
        logger.error("STEP 2: DATA TRANSFORMATION — Failed! (No raw data)")
        return False

    # Clean and transform the data
    cleaned_df = clean_and_transform(raw_data)
    if cleaned_df is None:
        logger.error("STEP 2: DATA TRANSFORMATION — Failed! (Transformation error)")
        return False

    # Display a preview of the cleaned data
    logger.info("\n--- Cleaned Data Preview ---")
    logger.info(f"\n{cleaned_df[['city', 'temperature', 'humidity', 'weather_condition']].to_string(index=False)}")

    # Save to CSV
    success = save_cleaned_data(cleaned_df)

    if success:
        logger.info("STEP 2: DATA TRANSFORMATION — Completed successfully! ✓")
    else:
        logger.error("STEP 2: DATA TRANSFORMATION — Failed!")

    return success


# This allows running the script standalone for testing
if __name__ == "__main__":
    run_transformation()
