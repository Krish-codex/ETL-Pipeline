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
            "aqi": raw_record.get("aqi"),
            "pm2_5": raw_record.get("pm2_5"),
            "pm10": raw_record.get("pm10"),
            "forecast_wind_speed": raw_record.get("forecast_wind_speed"),
            "forecast_humidity": raw_record.get("forecast_humidity"),
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
    """
    logger.info("Starting multi-stage data validation & cleaning...")

    total_anomalies_detected = 0

    # Stage 1: Extract fields from each record
    cleaned_records = []
    for i, record in enumerate(raw_data):
        cleaned = extract_weather_fields(record)
        if cleaned:
            cleaned_records.append(cleaned)
        else:
            total_anomalies_detected += 1
            logger.warning(f"Anomaly Fixed: Skipped record {i + 1} due to extraction failure")

    if not cleaned_records:
        logger.error("No records survived the cleaning process!")
        return None

    # Stage 2: Create a pandas DataFrame
    df = pd.DataFrame(cleaned_records)
    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")

    # Stage 3: Handle missing/null values for numeric columns
    numeric_cols = [
        "temperature", "feels_like", "humidity", "pressure", "wind_speed",
        "aqi", "pm2_5", "pm10", "forecast_wind_speed", "forecast_humidity"
    ]
    for col in numeric_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                total_anomalies_detected += missing_count
                median_value = df[col].median()
                # If median is NaN (entire column is empty), fill with 0 or standard base
                if pd.isna(median_value):
                    median_value = 0.0
                df[col] = df[col].fillna(median_value)
                logger.info(f"Anomaly Fixed: Filled {missing_count} missing values in '{col}' with median: {median_value}")

    # Stage 4: Handle missing/null values for text columns
    text_cols = ["city", "weather_condition", "weather_description", "country"]
    for col in text_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                total_anomalies_detected += missing_count
                df[col] = df[col].fillna("Unknown")
                logger.info(f"Anomaly Fixed: Filled {missing_count} missing values in '{col}' with 'Unknown'")

    # Stage 5: Convert and enforce exact data types (Type checking validation stage)
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")
    df["aqi"] = pd.to_numeric(df["aqi"], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Handle any conversion failures that resulted in new nulls
    for col in ["temperature", "humidity", "aqi"]:
        conversion_failures = df[col].isna().sum()
        if conversion_failures > 0:
            total_anomalies_detected += conversion_failures
            df[col] = df[col].fillna(0)
            logger.info(f"Anomaly Fixed: Resolved {conversion_failures} invalid type entries in '{col}'")

    # Stage 6: Value Range checks (e.g. temperatures or AQI cannot be negative/out-of-bounds)
    if "temperature" in df.columns:
        out_of_bounds_temp = df[(df["temperature"] > 60) | (df["temperature"] < -60)]
        if len(out_of_bounds_temp) > 0:
            total_anomalies_detected += len(out_of_bounds_temp)
            df.loc[df["temperature"] > 60, "temperature"] = 35.0
            df.loc[df["temperature"] < -60, "temperature"] = -10.0
            logger.info(f"Anomaly Fixed: Standardized {len(out_of_bounds_temp)} extreme/out-of-bound temperatures")

    # Stage 7: Add derived/calculated columns
    df["temp_category"] = pd.cut(
        df["temperature"],
        bins=[-float("inf"), 0, 15, 25, 35, float("inf")],
        labels=["Freezing", "Cold", "Mild", "Warm", "Hot"],
    )

    # Round numeric columns to 2 decimal places
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].round(2)

    # Stage 8: Remove duplicate entries
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["city"], keep="last")
    after_dedup = len(df)
    duplicates = before_dedup - after_dedup
    if duplicates > 0:
        total_anomalies_detected += duplicates
        logger.info(f"Anomaly Fixed: Dropped {duplicates} duplicate city records")

    logger.info(f"🎯 Multi-stage validation complete! Successfully resolved {total_anomalies_detected} anomalies.")
    logger.info(f"Final cleaned DataFrame shape: {df.shape}")
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
