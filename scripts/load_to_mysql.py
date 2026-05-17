"""
STEP 3 & 4 — Load Cleaned Data into MySQL Database (with SQLite Fallback)
=======================================================================
This script handles the 'Load' part of our ETL pipeline.

What it does:
- Connects to MySQL server using credentials in config.py
- If MySQL is down or credentials are not configured:
  It automatically falls back to SQLite so the pipeline can be executed
  and reviewed end-to-end without needing a running database server!
- Creates the database and table schema (using create_table.sql)
- Reads the cleaned CSV data from the Transform step
- Inserts data into the table using safe, parameterized queries

As an intern, I wanted to make this project super robust and 'plug-and-play' for
reviewers on GitHub. If they don't have MySQL installed/running, they won't get
errors — the pipeline will gracefully switch to SQLite and keep running!
"""

import os
import sqlite3
import sys

import mysql.connector
import pandas as pd
from mysql.connector import Error

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CLEANED_DATA_PATH, MYSQL_CONFIG, SQL_DIR, SQLITE_DB_PATH
from scripts.logger_setup import get_logger

# Initialize logger for this module
logger = get_logger("load_to_mysql")

# Flag to track whether we fell back to SQLite
USE_SQLITE = False


def check_mysql_availability() -> bool:
    """
    Checks if a local MySQL instance is reachable with configured credentials.
    """
    global USE_SQLITE
    try:
        config = MYSQL_CONFIG.copy()
        config.pop("database", None)  # Connect to server, not specific DB yet
        config["use_pure"] = True      # Avoid C-extension DLL conflicts on Windows
        
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            connection.close()
            USE_SQLITE = False
            return True
    except Exception:
        # If MySQL connection fails, we log it and set SQLite fallback
        USE_SQLITE = True
        return False
    return False


def get_mysql_connection(use_database: bool = True):
    """
    Creates and returns a MySQL database connection.
    """
    try:
        config = MYSQL_CONFIG.copy()
        config["use_pure"] = True      # Avoid C-extension DLL conflicts on Windows
        if not use_database:
            config.pop("database", None)

        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"MySQL connection error: {e}")
        return None


def get_sqlite_connection():
    """
    Creates and returns a SQLite database connection.
    """
    try:
        # Create parent dir for database if it doesn't exist
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        connection = sqlite3.connect(SQLITE_DB_PATH)
        return connection
    except sqlite3.Error as e:
        logger.error(f"SQLite connection error: {e}")
        return None


def create_database_and_table() -> bool:
    """
    Creates database and table. Supports both MySQL and SQLite.
    """
    global USE_SQLITE
    
    if check_mysql_availability():
        logger.info("MySQL Server detected! Setting up MySQL schema...")
        connection = get_mysql_connection(use_database=False)
        if not connection:
            logger.warning("Could not establish MySQL connection. Trying SQLite fallback...")
            USE_SQLITE = True
        else:
            try:
                cursor = connection.cursor()
                cursor.execute("CREATE DATABASE IF NOT EXISTS weather_pipeline")
                cursor.execute("USE weather_pipeline")
                
                # Load from sql file
                sql_file_path = os.path.join(SQL_DIR, "create_table.sql")
                if os.path.exists(sql_file_path):
                    with open(sql_file_path, "r", encoding="utf-8") as f:
                        sql_script = f.read()
                    
                    # Split queries by semicolon and run them
                    for statement in sql_script.split(";"):
                        statement = statement.strip()
                        if statement:
                            cursor.execute(statement)
                    logger.info("MySQL table setup complete via SQL DDL script.")
                connection.commit()
                cursor.close()
                connection.close()
                return True
            except Error as e:
                logger.error(f"Error setting up MySQL: {e}. Falling back to SQLite...")
                USE_SQLITE = True
                if connection.is_connected():
                    connection.close()
    else:
        logger.warning(
            "MySQL Server not reachable or password wrong! "
            "Falling back to local SQLite DB: data/weather_pipeline.db"
        )
        USE_SQLITE = True

    if USE_SQLITE:
        logger.info("Setting up SQLite schema...")
        connection = get_sqlite_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            # SQLite compatible table structure
            create_table_query = """
            CREATE TABLE IF NOT EXISTS weather_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                temperature REAL,
                feels_like REAL,
                temp_min REAL,
                temp_max REAL,
                humidity INTEGER,
                pressure INTEGER,
                weather_condition TEXT,
                weather_description TEXT,
                wind_speed REAL,
                visibility INTEGER,
                country TEXT,
                temp_category TEXT,
                timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            connection.commit()
            cursor.close()
            connection.close()
            logger.info("SQLite table setup complete successfully! ✓")
            return True
        except sqlite3.Error as e:
            logger.error(f"SQLite setup error: {e}")
            return False


def load_csv_to_db() -> bool:
    """
    Reads the cleaned CSV and inserts it into the database (MySQL or SQLite).
    """
    global USE_SQLITE

    try:
        if not os.path.exists(CLEANED_DATA_PATH):
            logger.error(f"Cleaned CSV not found at: {CLEANED_DATA_PATH}. Run Step 2 first.")
            return False

        df = pd.read_csv(CLEANED_DATA_PATH)
        logger.info(f"Loaded {len(df)} records from cleaned CSV.")

        if df.empty:
            logger.warning("Cleaned CSV is empty. Nothing to load.")
            return False

        if not USE_SQLITE:
            # MySQL loading flow
            connection = get_mysql_connection(use_database=True)
            if not connection:
                logger.error("Could not connect to MySQL database.")
                return False
            
            cursor = connection.cursor()
            cursor.execute("DELETE FROM weather_data")
            
            insert_query = """
            INSERT INTO weather_data 
                (city, temperature, feels_like, temp_min, temp_max,
                 humidity, pressure, weather_condition, weather_description,
                 wind_speed, visibility, country, temp_category, timestamp)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            records = []
            for _, row in df.iterrows():
                record = tuple(
                    None if pd.isna(val) else val
                    for val in [
                        row.get("city"), row.get("temperature"), row.get("feels_like"),
                        row.get("temp_min"), row.get("temp_max"), row.get("humidity"),
                        row.get("pressure"), row.get("weather_condition"),
                        row.get("weather_description"), row.get("wind_speed"),
                        row.get("visibility"), row.get("country"),
                        row.get("temp_category"), row.get("timestamp")
                    ]
                )
                records.append(record)

            cursor.executemany(insert_query, records)
            connection.commit()
            logger.info(f"Loaded {cursor.rowcount} records into MySQL database successfully!")
            cursor.close()
            connection.close()
            return True

        else:
            # SQLite loading flow
            connection = get_sqlite_connection()
            if not connection:
                logger.error("Could not connect to SQLite database.")
                return False
            
            cursor = connection.cursor()
            cursor.execute("DELETE FROM weather_data")
            
            # SQLite uses ? placeholders instead of %s
            insert_query = """
            INSERT INTO weather_data 
                (city, temperature, feels_like, temp_min, temp_max,
                 humidity, pressure, weather_condition, weather_description,
                 wind_speed, visibility, country, temp_category, timestamp)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            records = []
            for _, row in df.iterrows():
                record = tuple(
                    None if pd.isna(val) else val
                    for val in [
                        row.get("city"), row.get("temperature"), row.get("feels_like"),
                        row.get("temp_min"), row.get("temp_max"), row.get("humidity"),
                        row.get("pressure"), row.get("weather_condition"),
                        row.get("weather_description"), row.get("wind_speed"),
                        row.get("visibility"), row.get("country"),
                        row.get("temp_category"), row.get("timestamp")
                    ]
                )
                records.append(record)

            cursor.executemany(insert_query, records)
            connection.commit()
            logger.info(f"Loaded {len(records)} records into SQLite database successfully! ✓")
            cursor.close()
            connection.close()
            return True

    except Exception as e:
        logger.error(f"Error during loading step: {e}")
        return False


def run_loading() -> bool:
    """
    Main function for loading stage.
    """
    logger.info("=" * 60)
    logger.info("STEP 3-4: DATABASE SETUP & DATA LOADING — Starting...")
    logger.info("=" * 60)

    if not create_database_and_table():
        logger.error("Database setup failed.")
        return False

    success = load_csv_to_db()
    if success:
        logger.info("STEP 3-4: DATABASE SETUP & DATA LOADING — Completed successfully! ✓")
    else:
        logger.error("STEP 3-4: DATABASE SETUP & DATA LOADING — Failed!")
    return success


if __name__ == "__main__":
    run_loading()
