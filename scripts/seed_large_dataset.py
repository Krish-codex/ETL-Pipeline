"""
STEP 5 — Seed Large Benchmark Dataset (50,000+ records)
=========================================================
This script generates a realistic historical weather and air quality dataset
spanning 2+ years for all 10 cities. It seeds either MySQL or SQLite
to enable testing SQL performance optimizations (JOINs, Window Functions)
on a production-scale database.

This directly addresses the resume highlight:
"Optimised SQL reporting queries (JOINS, GROUP BY, window functions),
cutting average execution time from ~4s to under 1s on 50K-row tables."
"""

import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CITIES, CITY_COORDINATES
from scripts.logger_setup import get_logger
from scripts.load_to_mysql import get_sqlite_connection, check_mysql_availability, get_mysql_connection

logger = get_logger("seed_large_dataset")

def generate_historical_data() -> pd.DataFrame:
    """
    Generates 51,100 realistic weather history records over 730 days.
    """
    logger.info("Generating 51,100 records of high-fidelity historical weather data...")
    
    city_bases = {
        "Mumbai": {"temp": 28.0, "humidity": 75, "weather": "Rain", "desc": "moderate rain", "country": "IN"},
        "Delhi": {"temp": 25.0, "humidity": 45, "weather": "Haze", "desc": "haze", "country": "IN"},
        "London": {"temp": 12.0, "humidity": 80, "weather": "Clouds", "desc": "broken clouds", "country": "GB"},
        "New York": {"temp": 14.0, "humidity": 65, "weather": "Clear", "desc": "clear sky", "country": "US"},
        "Tokyo": {"temp": 16.0, "humidity": 68, "weather": "Clouds", "desc": "scattered clouds", "country": "JP"},
        "Sydney": {"temp": 18.0, "humidity": 70, "weather": "Clear", "desc": "clear sky", "country": "AU"},
        "Dubai": {"temp": 33.0, "humidity": 35, "weather": "Clear", "desc": "clear sky", "country": "AE"},
        "Paris": {"temp": 13.0, "humidity": 73, "weather": "Mist", "desc": "mist", "country": "FR"},
        "Berlin": {"temp": 11.0, "humidity": 70, "weather": "Clouds", "desc": "few clouds", "country": "DE"},
        "Toronto": {"temp": 8.0, "humidity": 65, "weather": "Clear", "desc": "clear sky", "country": "CA"},
    }
    
    records = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days=730)
    
    # 7 intervals per day over 730 days for 10 cities = 51,100 rows
    intervals_per_day = 7
    total_days = 730
    
    for city in CITIES:
        base = city_bases.get(city)
        logger.info(f"Generating history for {city}...")
        
        for d in range(total_days):
            day_date = start_time + timedelta(days=d)
            # Seasonal variation (sine wave over the year)
            day_of_year = day_date.timetuple().tm_yday
            seasonal_temp_offset = 8.0 * random.uniform(0.8, 1.2) * (1.0 - 2.0 * abs(day_of_year - 180) / 365)
            
            for hour_idx in range(intervals_per_day):
                hour = hour_idx * 3.4  # Spread across the day
                timestamp = day_date.replace(hour=int(hour), minute=int((hour % 1) * 60))
                
                # Diurnal variation (warmest in afternoon)
                diurnal_offset = 4.0 * (1.0 - abs(hour - 14.0) / 10.0)
                
                temp = round(base["temp"] + seasonal_temp_offset + diurnal_offset + random.uniform(-2.0, 2.0), 2)
                humidity = int(max(10, min(100, base["humidity"] - seasonal_temp_offset * 1.5 + random.randint(-8, 8))))
                feels_like = round(temp + (0.2 if humidity > 70 else -0.2), 2)
                pressure = random.randint(1005, 1025)
                wind_speed = round(random.uniform(1.0, 9.0) + (1.5 if seasonal_temp_offset > 3 else 0), 2)
                
                # Air quality variations (Delhi / Mumbai higher)
                aqi_base = 150 if city == "Delhi" else (80 if city == "Mumbai" else 30)
                aqi = int(max(10, aqi_base + random.randint(-20, 50)))
                pm2_5 = round(aqi * random.uniform(0.12, 0.28), 2)
                pm10 = round(aqi * random.uniform(0.25, 0.45), 2)
                
                forecast_wind = round(wind_speed * random.uniform(0.8, 1.2), 2)
                forecast_hum = int(max(10, min(100, humidity + random.randint(-5, 5))))
                
                # Temperature category
                if temp < 0:
                    cat = "Freezing"
                elif temp <= 15:
                    cat = "Cold"
                elif temp <= 25:
                    cat = "Mild"
                elif temp <= 35:
                    cat = "Warm"
                else:
                    cat = "Hot"
                
                records.append({
                    "city": city,
                    "country": base["country"],
                    "temperature": temp,
                    "feels_like": feels_like,
                    "temp_min": round(temp - 1.5, 2),
                    "temp_max": round(temp + 1.5, 2),
                    "humidity": humidity,
                    "pressure": pressure,
                    "weather_condition": base["weather"],
                    "weather_description": base["desc"],
                    "wind_speed": wind_speed,
                    "visibility": random.randint(8000, 10000),
                    "aqi": aqi,
                    "pm2_5": pm2_5,
                    "pm10": pm10,
                    "forecast_wind_speed": forecast_wind,
                    "forecast_humidity": forecast_hum,
                    "temp_category": cat,
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
                })
                
    df = pd.DataFrame(records)
    logger.info(f"Successfully generated {len(df)} records in DataFrame.")
    return df

def seed_database(df: pd.DataFrame):
    """
    Seeds the dataframe into MySQL or SQLite depending on availability.
    """
    use_sqlite = not check_mysql_availability()
    db_name = "SQLite" if use_sqlite else "MySQL"
    logger.info(f"Targeting database engine: {db_name} for seeding...")

    if not use_sqlite:
        connection = get_mysql_connection(use_database=True)
        if not connection:
            logger.warning("MySQL connection failed. Seeding fallback to SQLite...")
            use_sqlite = True
        else:
            try:
                cursor = connection.cursor()
                
                # Clear measurements to ensure fresh seed
                logger.info("Clearing existing measurements in MySQL...")
                cursor.execute("DELETE FROM fact_weather_measurements")
                
                # Insert cities
                city_insert_query = "INSERT IGNORE INTO dim_cities (city_name, country) VALUES (%s, %s)"
                city_records = list(set([(row["city"], row["country"]) for _, row in df.iterrows()]))
                cursor.executemany(city_insert_query, city_records)
                connection.commit()
                
                # Get city maps
                cursor.execute("SELECT city_id, city_name FROM dim_cities")
                city_map = {name: cid for cid, name in cursor.fetchall()}
                
                # Bulk insert into fact table
                logger.info("Bulk-inserting 50,000+ historical records into MySQL...")
                fact_insert_query = """
                INSERT INTO fact_weather_measurements 
                    (city_id, temperature, feels_like, temp_min, temp_max,
                     humidity, pressure, weather_condition, weather_description,
                     wind_speed, visibility, aqi, pm2_5, pm10, 
                     forecast_wind_speed, forecast_humidity, temp_category, timestamp)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                records = []
                for _, row in df.iterrows():
                    city_id = city_map[row["city"]]
                    record = tuple(
                        None if pd.isna(val) else val
                        for val in [
                            city_id, row["temperature"], row["feels_like"],
                            row.get("temp_min"), row.get("temp_max"), row["humidity"],
                            row["pressure"], row["weather_condition"],
                            row["weather_description"], row["wind_speed"],
                            row["visibility"], row["aqi"], row["pm2_5"],
                            row["pm10"], row["forecast_wind_speed"],
                            row["forecast_humidity"], row["temp_category"],
                            row["timestamp"]
                        ]
                    )
                    records.append(record)
                
                # Execute in batches to prevent payload limits
                batch_size = 5000
                total_inserted = 0
                for idx in range(0, len(records), batch_size):
                    batch = records[idx : idx + batch_size]
                    cursor.executemany(fact_insert_query, batch)
                    total_inserted += cursor.rowcount
                    logger.info(f"MySQL Batch Seeding: Inserted {total_inserted}/{len(records)} records...")
                
                connection.commit()
                logger.info("MySQL Seeding complete! Database is now populated with 51,100 records. ✓")
                cursor.close()
                connection.close()
                return
            except Exception as e:
                logger.error(f"MySQL seeding error: {e}. Falling back to SQLite...")
                use_sqlite = True
                if connection.is_connected():
                    connection.close()

    if use_sqlite:
        connection = get_sqlite_connection()
        if not connection:
            logger.error("Could not establish SQLite connection.")
            return
        
        try:
            cursor = connection.cursor()
            
            # Clear old records
            logger.info("Clearing existing measurements in SQLite...")
            cursor.execute("DELETE FROM fact_weather_measurements")
            
            # Insert cities
            city_insert_query = "INSERT OR IGNORE INTO dim_cities (city_name, country) VALUES (?, ?)"
            city_records = list(set([(row["city"], row["country"]) for _, row in df.iterrows()]))
            cursor.executemany(city_insert_query, city_records)
            connection.commit()
            
            # Get city maps
            cursor.execute("SELECT city_id, city_name FROM dim_cities")
            city_map = {name: cid for cid, name in cursor.fetchall()}
            
            # Bulk insert fact table
            logger.info("Bulk-inserting 50,000+ historical records into SQLite...")
            fact_insert_query = """
            INSERT INTO fact_weather_measurements 
                (city_id, temperature, feels_like, temp_min, temp_max,
                 humidity, pressure, weather_condition, weather_description,
                 wind_speed, visibility, aqi, pm2_5, pm10, 
                 forecast_wind_speed, forecast_humidity, temp_category, timestamp)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            records = []
            for _, row in df.iterrows():
                city_id = city_map[row["city"]]
                record = tuple(
                    None if pd.isna(val) else val
                    for val in [
                        city_id, row["temperature"], row["feels_like"],
                        row.get("temp_min"), row.get("temp_max"), row["humidity"],
                        row["pressure"], row["weather_condition"],
                        row["weather_description"], row["wind_speed"],
                        row["visibility"], row["aqi"], row["pm2_5"],
                        row["pm10"], row["forecast_wind_speed"],
                        row["forecast_humidity"], row["temp_category"],
                        row["timestamp"]
                    ]
                )
                records.append(record)
            
            # Batch insertion for SQLite
            batch_size = 5000
            total_inserted = 0
            for idx in range(0, len(records), batch_size):
                batch = records[idx : idx + batch_size]
                cursor.executemany(fact_insert_query, batch)
                total_inserted += len(batch)
                logger.info(f"SQLite Batch Seeding: Inserted {total_inserted}/{len(records)} records...")
            
            connection.commit()
            logger.info("SQLite Seeding complete! Database is now populated with 51,100 records. ✓")
            cursor.close()
            connection.close()
            
        except sqlite3.Error as e:
            logger.error(f"SQLite seeding failed: {e}")

if __name__ == "__main__":
    df = generate_historical_data()
    seed_database(df)
