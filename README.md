# 🌦️ Production-Grade Automated ETL Pipeline & Relational SQL Reporting

> A production-grade **Extract, Transform, Load (ETL)** pipeline that ingests real-time climatological, air-quality, and meteorological data from **3 public REST APIs** for 10 global cities. Data is cleaned via a multi-stage Pandas validation pipeline, incrementally loaded into a **3NF normalized database schema (MySQL/SQLite)**, and analyzed using advanced relational **SQL JOINs and Window Functions** over a **51,100-row historical benchmark dataset**—all automated in the cloud via **GitHub Actions**.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3.25+-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Cloud_Scheduler-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

---

## 📌 Project Architecture

This architecture mirrors a **real-world production data engineering workflow**. Instead of executing on unreliable local machines, the ingestion pipeline runs completely in the cloud, generating self-sustaining historical databases and automatic portfolio commits daily.

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 GITHUB ACTIONS CLOUD RUNNER            │
                  │              (Executes Daily at 9:30 PM IST)           │
                  └───────────────────────────┬────────────────────────────┘
                                              │
                                              ▼
 ┌──────────────────────┐          ┌──────────────────────┐          ┌──────────────────────┐
 │   API 1: OpenWeather │          │ API 2: Open-Meteo AQ │          │ API 3: Open-Meteo FC │
 │  (Current Climate)   │          │ (Air Quality Index)  │          │ (Meteorology Forecast)│
 └──────────┬───────────┘          └──────────┬───────────┘          └──────────┬───────────┘
            │                                 │                                 │
            └─────────────────────────────────┼─────────────────────────────────┘
                                              ▼
                                 ┌─────────────────────────┐
                                 │ Multi-Stage Validation  │ (Type conformance, median nulls,
                                 │   & Anomaly Auditing    │  out-of-bounds capping, drops)
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   Incremental Loader    │ (Key mapping, INSERT IGNORE,
                                 │  (MySQL/SQLite Engine)  │  composite UNIQUE constraint)
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   Normalized Database   │ (Stored in Git repository at
                                 │  (3NF Relational DDL)   │  data/weather_pipeline.db)
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │ SQL Window Functioning  │ (RANK, DENSE_RANK, averages,
                                 │    & Query Reporting    │  compiled to outputs/results.txt)
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │  Automated Cloud Push   │ (Pushed back to github.com
                                 │   (github-actions bot)  │  even if laptop is off!)
                                 └─────────────────────────┘
```

---

## ✨ Enterprise Features

- **Multi-API Data Ingestion**: Concurrently queries **3 REST APIs** (OpenWeather, Open-Meteo Air Quality, and Open-Meteo Weather Forecast) compiling detailed climate, pollution (PM2.5, PM10), and forecasting matrices.
- **Robust Ingestion Resilience**: Ingestion adapter built on top of requests `Session` objects integrated with a strict `urllib3.util.Retry` adapter. Handles transient gateway timeouts, drops, and server crashes via **exponential backoff retries** (1s, 2s, 4s delay).
- **Multi-Stage Pandas Anomaly Logging**: Validates raw datasets through six stages (schema type coercion, median null imputation, out-of-bound capping, deduplication, and complete metric logging). Quantifies exact validation statistics on every run.
- **3NF Database Normalization**: Structures database schemas programmatically in third normal form using MySQL with a local SQLite offline fallback. Divides flat records into dimension table `dim_cities` and indexed fact table `fact_weather_measurements`.
- **Composite Unique Database Constraints**: Prevents database duplication across recurrent execution runs via a unique composite index `uq_city_timestamp (city_id, timestamp)` inside the fact table, coupled with safe `INSERT IGNORE` (MySQL) and `INSERT OR IGNORE` (SQLite) loaders.
- **Advanced SQL Query Reporting**: Employs complex relational queries utilizing `INNER JOIN`s, `GROUP BY` aggregations, and window functions including `RANK() OVER (...)` to rank wind speeds per country, `DENSE_RANK() OVER (...)` to rank global pollution levels, and cumulative/moving windows to track historical averages in under 0.6 seconds.
- **Production-scale Benchmarking**: Features a historical seeder script generating **51,100 high-fidelity time-series records** over a 2-year period, allowing immediate demonstration of indexing and query speed optimization (cutting speeds from ~4s to under 0.6s).
- **Scheduled Cloud Commits**: Fully automated via GitHub Actions scheduled cron runs executing **every night at 9:30 PM IST**, compiling, loading, and committing databases and reports to GitHub completely independent of your local machine.

---

## 🗄️ Database Design (3NF Schema)

The database schema is structured to optimize relational integrity and indexing lookup speeds:

### 1. Dimension Cities Table (`dim_cities`)
Stores unique geographical dimensions for monitored cities:
```sql
CREATE TABLE dim_cities (
    city_id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(10) NOT NULL
);
```

### 2. Fact Weather Measurements Table (`fact_weather_measurements`)
Stores continuous time-series metrics linked back to dimensions:
```sql
CREATE TABLE fact_weather_measurements (
    measurement_id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    temperature DECIMAL(5, 2),
    feels_like DECIMAL(5, 2),
    temp_min DECIMAL(5, 2),
    temp_max DECIMAL(5, 2),
    humidity INT,
    pressure INT,
    weather_condition VARCHAR(50),
    weather_description VARCHAR(100),
    wind_speed DECIMAL(5, 2),
    visibility INT,
    aqi INT,                   -- Air Quality API
    pm2_5 DECIMAL(5, 2),       -- Air Quality API
    pm10 DECIMAL(5, 2),        -- Air Quality API
    forecast_wind_speed DECIMAL(5, 2),  -- Forecast API
    forecast_humidity INT,               -- Forecast API
    temp_category VARCHAR(20), -- Derived Validation field
    timestamp DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city_id) REFERENCES dim_cities(city_id),
    UNIQUE KEY uq_city_timestamp (city_id, timestamp),
    INDEX idx_city_id (city_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_weather (weather_condition)
);
```

---

## 📅 Where and How is the Historical Database Saved?

1. **Where is it stored?**
   * Locally, the entire active time-series weather history is stored in a structured SQLite database file at **`data/weather_pipeline.db`**.
2. **How is it updated and saved on GitHub?**
   * At exactly **9:30 PM IST every single day**, the GitHub Actions scheduler spins up a virtual runner and executes the ETL pipeline.
   * The pipeline appends the daily real-time weather metrics safely into the database file, generating the latest analytical query report.
   * The GitHub Actions robot automatically executes a Git commit and pushes the updated binary **`data/weather_pipeline.db`** file and analytical report text **`outputs/analysis_results.txt`** directly back to your GitHub repository on `github.com`.
   * **Your laptop can be completely off**; when you boot up, simply run `git pull` to download the updated history compiled while you slept!

---

## ▶️ Setup & Execution Instructions

### Prerequisites
- Python 3.10+
- MySQL Server 8.0+ (Optional; falls back to SQLite automatically if local offline)
- OpenWeather API Key (Free tier, optional; runs in simulation mode if not provided)

### 1. Installation & Configurations
```bash
# Clone the repository
git clone https://github.com/Krish-codex/ETL-Pipeline.git
cd ETL-Pipeline

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Ingestion & Normalization Schema Setup
This programmatically initializes the MySQL/SQLite database tables, dimension mappings, and indexes:
```bash
python main.py --step 3
```

### 3. Populate the 51,100-Row Historical Benchmark
Generate and bulk-insert a 2-year high-fidelity weather, pollution, and forecast history across all 10 monitored cities to test database performance:
```bash
python scripts/seed_large_dataset.py
```

### 4. Run the Full ETL Pipeline Live
Fetches current measurements from all 3 APIs, transforms data, executes incremental loading, and outputs the report:
```bash
python main.py
```
*The full end-to-end execution on 51,110 rows completes in **under 0.8 seconds**!*

### 5. Launch the Streamlit Interactive Dashboard
Run the analytics dashboard with Plotly charts visualizing trends from the relational database:
```bash
streamlit run dashboard.py
```

---

## 📊 Sample SQL Reporting Results (outputs/analysis_results.txt)

```
======================================================================
  Rank Cities by Wind Speed in Each Country (Window Function RANK & JOIN)
======================================================================
  City        Country  Wind Speed (m/s)  Rank in Country 
  --------------------------------------------------------
  Delhi       IN       8.77              1               
  Mumbai      IN       8.68              2               
  London      GB       9.84              1               
  New York    US       9.61              1               

======================================================================
  Top Windiest and Polluted Cities (JOIN & Window Function DENSE_RANK)
======================================================================
  City        Country  AQI  Global AQI Rank 
  -------------------------------------------
  Delhi       IN       199  1               
  Delhi       IN       198  2               
  Delhi       IN       197  3               
  Delhi       IN       196  4               

======================================================================
  Weather Summary Statistics (Aggregations on Fact Table)
======================================================================
  Total Records  Unique Cities  Avg Temp (°C)  Avg Humidity (%)  Avg AQI  
  ------------------------------------------------------------------------
  51110          10             23.19          58.13             62.06    
```

---

## 🧠 Core Learnings & Architecture Defense
Building this production ETL pipeline demonstrated key data engineering patterns:
1. **API Tolerance**: Managing transient network outages in high-throughput scripting via session reuse and exponential backoff policies.
2. **Schema Integrity**: Transforming flat files to a highly optimized normalized database (3NF) ensuring referential constraints.
3. **Optimized SQL**: Demonstrating execution query tuning on 50,000+ records via compound indexing and writing high-performance Window Functions (`RANK`, `DENSE_RANK`).
4. **DevOps Automation**: Automating data-ingestion workflows independent of hardware availability via cron-scheduled GitHub Actions runners.
