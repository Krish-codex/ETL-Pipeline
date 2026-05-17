"""
STEP 5 — SQL Analysis (Run Analytical Queries on the Data)
============================================================
This script runs SQL queries against the loaded weather data to
generate meaningful insights about weather patterns.

What it does:
- Automatically detects if the data was loaded into MySQL or SQLite
- Connects to the appropriate active database
- Runs various analytical SQL queries (AVG, COUNT, GROUP BY, etc.)
- Formats the results into highly readable text tables
- Saves the analysis report to outputs/analysis_results.txt

I wanted this analysis step to be extremely resilient, so if the load step fell
back to SQLite, this script will automatically connect to SQLite and run
the equivalent queries without breaking!
"""

import os
import sqlite3
import sys
from datetime import datetime

import mysql.connector
from mysql.connector import Error

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANALYSIS_OUTPUT_PATH, MYSQL_CONFIG, OUTPUT_DIR, SQLITE_DB_PATH
from scripts.logger_setup import get_logger

# Initialize logger for this module
logger = get_logger("analyze_data")

# ==============================
# SQL ANALYSIS QUERIES (MySQL)
# ==============================
MYSQL_QUERIES = [
    (
        "Average Temperature by City",
        """
        SELECT city, 
               ROUND(AVG(temperature), 2) AS avg_temp,
               ROUND(MIN(temperature), 2) AS min_temp,
               ROUND(MAX(temperature), 2) AS max_temp
        FROM weather_data
        GROUP BY city
        ORDER BY avg_temp DESC
        """,
        ["City", "Avg Temp (°C)", "Min Temp (°C)", "Max Temp (°C)"],
    ),
    (
        "Average Humidity by City",
        """
        SELECT city,
               ROUND(AVG(humidity), 2) AS avg_humidity
        FROM weather_data
        GROUP BY city
        ORDER BY avg_humidity DESC
        """,
        ["City", "Avg Humidity (%)"],
    ),
    (
        "Most Common Weather Conditions",
        """
        SELECT weather_condition,
               COUNT(*) AS occurrence_count,
               GROUP_CONCAT(DISTINCT city ORDER BY city SEPARATOR ', ') AS cities
        FROM weather_data
        GROUP BY weather_condition
        ORDER BY occurrence_count DESC
        """,
        ["Weather Condition", "Count", "Cities"],
    ),
    (
        "Temperature Categories Distribution",
        """
        SELECT temp_category,
               COUNT(*) AS city_count,
               ROUND(AVG(temperature), 2) AS avg_temp,
               ROUND(AVG(humidity), 2) AS avg_humidity
        FROM weather_data
        WHERE temp_category IS NOT NULL
        GROUP BY temp_category
        ORDER BY avg_temp DESC
        """,
        ["Category", "City Count", "Avg Temp (°C)", "Avg Humidity (%)"],
    ),
    (
        "Hottest and Coldest Cities",
        """
        (SELECT city, temperature, humidity, weather_condition, 'Hottest' AS label
         FROM weather_data
         ORDER BY temperature DESC LIMIT 3)
        UNION ALL
        (SELECT city, temperature, humidity, weather_condition, 'Coldest' AS label
         FROM weather_data
         ORDER BY temperature ASC LIMIT 3)
        """,
        ["City", "Temp (°C)", "Humidity (%)", "Weather", "Label"],
    ),
    (
        "Cities with High Wind Speed",
        """
        SELECT city, wind_speed, weather_condition, temperature
        FROM weather_data
        WHERE wind_speed IS NOT NULL
        ORDER BY wind_speed DESC
        LIMIT 5
        """,
        ["City", "Wind Speed (m/s)", "Weather", "Temp (°C)"],
    ),
    (
        "Weather Summary Statistics",
        """
        SELECT 
            COUNT(*) AS total_records,
            COUNT(DISTINCT city) AS unique_cities,
            ROUND(AVG(temperature), 2) AS overall_avg_temp,
            ROUND(AVG(humidity), 2) AS overall_avg_humidity,
            ROUND(AVG(wind_speed), 2) AS overall_avg_wind
        FROM weather_data
        """,
        ["Total Records", "Unique Cities", "Avg Temp (°C)", "Avg Humidity (%)", "Avg Wind (m/s)"],
    ),
    (
        "Country-wise Weather Overview",
        """
        SELECT country,
               COUNT(*) AS city_count,
               ROUND(AVG(temperature), 2) AS avg_temp,
               ROUND(AVG(humidity), 2) AS avg_humidity
        FROM weather_data
        GROUP BY country
        ORDER BY city_count DESC, avg_temp DESC
        """,
        ["Country", "Cities", "Avg Temp (°C)", "Avg Humidity (%)"],
    ),
]

# ===============================
# SQL ANALYSIS QUERIES (SQLite)
# ===============================
# We customize some query syntax because SQLite doesn't support features
# like GROUP_CONCAT with SEPARATOR or direct parentheses in UNIONs with LIMIT.
SQLITE_QUERIES = [
    (
        "Average Temperature by City",
        """
        SELECT city, 
               ROUND(AVG(temperature), 2) AS avg_temp,
               ROUND(MIN(temperature), 2) AS min_temp,
               ROUND(MAX(temperature), 2) AS max_temp
        FROM weather_data
        GROUP BY city
        ORDER BY avg_temp DESC
        """,
        ["City", "Avg Temp (°C)", "Min Temp (°C)", "Max Temp (°C)"],
    ),
    (
        "Average Humidity by City",
        """
        SELECT city,
               ROUND(AVG(humidity), 2) AS avg_humidity
        FROM weather_data
        GROUP BY city
        ORDER BY avg_humidity DESC
        """,
        ["City", "Avg Humidity (%)"],
    ),
    (
        "Most Common Weather Conditions",
        """
        SELECT weather_condition,
               COUNT(*) AS occurrence_count,
               GROUP_CONCAT(DISTINCT city) AS cities
        FROM weather_data
        GROUP BY weather_condition
        ORDER BY occurrence_count DESC
        """,
        ["Weather Condition", "Count", "Cities"],
    ),
    (
        "Temperature Categories Distribution",
        """
        SELECT temp_category,
               COUNT(*) AS city_count,
               ROUND(AVG(temperature), 2) AS avg_temp,
               ROUND(AVG(humidity), 2) AS avg_humidity
        FROM weather_data
        WHERE temp_category IS NOT NULL
        GROUP BY temp_category
        ORDER BY avg_temp DESC
        """,
        ["Category", "City Count", "Avg Temp (°C)", "Avg Humidity (%)"],
    ),
    (
        "Hottest and Coldest Cities",
        """
        SELECT * FROM (SELECT city, temperature, humidity, weather_condition, 'Hottest' AS label FROM weather_data ORDER BY temperature DESC LIMIT 3)
        UNION ALL
        SELECT * FROM (SELECT city, temperature, humidity, weather_condition, 'Coldest' AS label FROM weather_data ORDER BY temperature ASC LIMIT 3)
        """,
        ["City", "Temp (°C)", "Humidity (%)", "Weather", "Label"],
    ),
    (
        "Cities with High Wind Speed",
        """
        SELECT city, wind_speed, weather_condition, temperature
        FROM weather_data
        WHERE wind_speed IS NOT NULL
        ORDER BY wind_speed DESC
        LIMIT 5
        """,
        ["City", "Wind Speed (m/s)", "Weather", "Temp (°C)"],
    ),
    (
        "Weather Summary Statistics",
        """
        SELECT 
            COUNT(*) AS total_records,
            COUNT(DISTINCT city) AS unique_cities,
            ROUND(AVG(temperature), 2) AS overall_avg_temp,
            ROUND(AVG(humidity), 2) AS overall_avg_humidity,
            ROUND(AVG(wind_speed), 2) AS overall_avg_wind
        FROM weather_data
        """,
        ["Total Records", "Unique Cities", "Avg Temp (°C)", "Avg Humidity (%)", "Avg Wind (m/s)"],
    ),
    (
        "Country-wise Weather Overview",
        """
        SELECT country,
               COUNT(*) AS city_count,
               ROUND(AVG(temperature), 2) AS avg_temp,
               ROUND(AVG(humidity), 2) AS avg_humidity
        FROM weather_data
        GROUP BY country
        ORDER BY city_count DESC, avg_temp DESC
        """,
        ["Country", "Cities", "Avg Temp (°C)", "Avg Humidity (%)"],
    ),
]


def check_mysql_availability() -> bool:
    """Checks if a local MySQL instance is reachable with configured credentials."""
    try:
        config = MYSQL_CONFIG.copy()
        config["use_pure"] = True      # Avoid C-extension DLL conflicts on Windows
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            connection.close()
            return True
    except Exception:
        return False
    return False


def format_query_results(title: str, headers: list, rows: list) -> str:
    """
    Formats query results into a clean, readable text table.
    """
    output_lines = []
    output_lines.append(f"\n{'=' * 70}")
    output_lines.append(f"  {title}")
    output_lines.append(f"{'=' * 70}")

    if not rows:
        output_lines.append("  No data available for this query.")
        return "\n".join(output_lines)

    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(str(header))
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width + 2)

    header_line = "  " + "".join(
        str(h).ljust(w) for h, w in zip(headers, col_widths)
    )
    separator = "  " + "".join("-" * w for w in col_widths)

    output_lines.append(header_line)
    output_lines.append(separator)

    for row in rows:
        data_line = "  " + "".join(
            str(val).ljust(col_widths[i]) for i, val in enumerate(row)
        )
        output_lines.append(data_line)

    output_lines.append(f"\n  Records: {len(rows)}")
    return "\n".join(output_lines)


def run_analysis_queries() -> tuple[str, str]:
    """
    Executes all analysis queries and returns a tuple of (formatted_results, db_used).
    """
    use_sqlite = not check_mysql_availability()
    all_results = []
    db_used = "SQLite" if use_sqlite else "MySQL"

    if not use_sqlite:
        logger.info("Connecting to MySQL for data analysis...")
        try:
            config = MYSQL_CONFIG.copy()
            config["use_pure"] = True      # Avoid C-extension DLL conflicts on Windows
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            logger.info(f"Running {len(MYSQL_QUERIES)} analysis queries...")

            for title, query, headers in MYSQL_QUERIES:
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    formatted = format_query_results(title, headers, rows)
                    all_results.append(formatted)
                    logger.info(f"✓ {title} — {len(rows)} results")
                except Error as e:
                    logger.warning(f"Query failed: {title} — {e}")
                    all_results.append(f"\n{'=' * 70}\n  {title}\n{'=' * 70}\n  Query failed: {e}")
            
            cursor.close()
            connection.close()
            return "\n".join(all_results), db_used
            
        except Error as e:
            logger.error(f"MySQL connection failed during analysis: {e}. Falling back to SQLite...")
            use_sqlite = True
            db_used = "SQLite"

    if use_sqlite:
        logger.info(f"Connecting to SQLite ({SQLITE_DB_PATH}) for data analysis...")
        if not os.path.exists(SQLITE_DB_PATH):
            logger.error(f"SQLite database not found at: {SQLITE_DB_PATH}. Run loading step first.")
            return "", "None"
        
        try:
            connection = sqlite3.connect(SQLITE_DB_PATH)
            cursor = connection.cursor()
            logger.info(f"Running {len(SQLITE_QUERIES)} analysis queries...")

            for title, query, headers in SQLITE_QUERIES:
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    formatted = format_query_results(title, headers, rows)
                    all_results.append(formatted)
                    logger.info(f"✓ {title} — {len(rows)} results")
                except sqlite3.Error as e:
                    logger.warning(f"Query failed: {title} — {e}")
                    all_results.append(f"\n{'=' * 70}\n  {title}\n{'=' * 70}\n  Query failed: {e}")
            
            cursor.close()
            connection.close()
            return "\n".join(all_results), db_used
            
        except sqlite3.Error as e:
            logger.error(f"SQLite connection failed: {e}")
            return "", "None"


def save_analysis_results(results: str, db_used: str) -> bool:
    """
    Saves the formatted analysis results to outputs/analysis_results.txt.
    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        header = (
            f"{'#' * 70}\n"
            f"#  WEATHER DATA ANALYSIS REPORT\n"
            f"#  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"#  Database Backend: {db_used}\n"
            f"#  Pipeline: Automated ETL Pipeline using Python & MySQL\n"
            f"{'#' * 70}\n"
        )

        with open(ANALYSIS_OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(header)
            f.write(results)
            f.write(f"\n\n{'#' * 70}\n")
            f.write(f"#  END OF REPORT\n")
            f.write(f"{'#' * 70}\n")

        logger.info(f"Analysis results saved to: {ANALYSIS_OUTPUT_PATH}")
        return True

    except IOError as e:
        logger.error(f"Failed to save analysis results: {e}")
        return False


def run_analysis() -> bool:
    """
    Main function for the analysis stage.
    """
    logger.info("=" * 60)
    logger.info("STEP 5: SQL ANALYSIS — Starting...")
    logger.info("=" * 60)

    results, db_used = run_analysis_queries()

    if not results or db_used == "None":
        logger.error("STEP 5: SQL ANALYSIS — Failed! (No results generated)")
        return False

    success = save_analysis_results(results, db_used)
    if success:
        print(results)
        logger.info(f"STEP 5: SQL ANALYSIS — Completed successfully using {db_used}! ✓")
    else:
        logger.error("STEP 5: SQL ANALYSIS — Failed!")

    return success


if __name__ == "__main__":
    run_analysis()
