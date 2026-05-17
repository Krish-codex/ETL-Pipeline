# 🌦️ Automated ETL Pipeline using Python & MySQL

> A fully functional **Extract, Transform, Load (ETL)** pipeline that fetches real-time weather data from the OpenWeather API, cleans and structures it using Python & Pandas, loads it into a MySQL database, and generates analytical reports — all with a single command.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

---

## 📌 Project Overview

This project demonstrates a **real-world ETL workflow** commonly used in Data Engineering. It simulates how companies collect data from external APIs, clean it, store it in databases, and derive insights — all automated through Python.

### What is ETL?

| Step | Description |
|------|-------------|
| **Extract** | Fetch raw data from the OpenWeather API for 10+ cities |
| **Transform** | Clean, filter, and structure data using Pandas |
| **Load** | Insert processed data into a MySQL database |
| **Analyze** | Run SQL queries to generate meaningful insights |

---

## ✨ Features

- ✅ Real-time weather data extraction from OpenWeather API
- ✅ Raw JSON data preservation (data engineering best practice)
- ✅ Data cleaning with missing value handling using Pandas
- ✅ Derived columns (temperature categories, feels-like, etc.)
- ✅ MySQL database with indexed tables for fast queries
- ✅ 8 analytical SQL queries (AVG, GROUP BY, COUNT, UNION)
- ✅ Formatted analysis reports saved to text files
- ✅ Modular, well-documented Python codebase
- ✅ Comprehensive error handling and logging
- ✅ CLI support (`--step` flag to run individual steps)
- ✅ Interactive Streamlit dashboard with Plotly charts
- ✅ Automatic scheduling for periodic data refresh

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3.10+ | Core programming language |
| MySQL 8.0 | Relational database for data storage |
| Pandas | Data manipulation and cleaning |
| Requests | HTTP calls to weather API |
| mysql-connector-python | Python-MySQL connectivity |
| Streamlit | Interactive web dashboard |
| Plotly | Interactive data visualizations |
| Schedule | Automated pipeline execution |

---

## 📂 Project Structure

```
ETL-Pipeline/
│
├── data/                          # Data storage
│   ├── raw_weather_data.json      # Raw API responses (auto-generated)
│   └── cleaned_weather_data.csv   # Cleaned & structured data (auto-generated)
│
├── scripts/                       # Modular pipeline scripts
│   ├── __init__.py                # Package initializer
│   ├── logger_setup.py            # Centralized logging configuration
│   ├── fetch_data.py              # Step 1: API data extraction
│   ├── clean_data.py              # Step 2: Data transformation
│   ├── load_to_mysql.py           # Step 3-4: MySQL loading
│   └── analyze_data.py            # Step 5: SQL analysis
│
├── sql/
│   └── create_table.sql           # Database & table DDL
│
├── outputs/
│   └── analysis_results.txt       # Generated analysis report
│
├── logs/                          # Pipeline execution logs (auto-generated)
│
├── config.py                      # Centralized configuration
├── main.py                        # Pipeline orchestrator (entry point)
├── dashboard.py                   # Streamlit analytics dashboard
├── scheduler.py                   # Automatic scheduling
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10 or higher
- MySQL Server 8.0 or higher
- OpenWeather API key (free tier)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/etl-pipeline-weather.git
cd etl-pipeline-weather
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get OpenWeather API Key

1. Go to [https://openweathermap.org/api](https://openweathermap.org/api)
2. Sign up for a free account
3. Navigate to **API Keys** section
4. Copy your API key

### 5. Configure the Project

Open `config.py` and update:

```python
# Replace with your actual API key
OPENWEATHER_API_KEY = "your_api_key_here"

# Replace with your MySQL credentials
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "weather_pipeline",
}
```

Alternatively, set the API key as an environment variable:

```bash
# Windows (PowerShell)
$env:OPENWEATHER_API_KEY = "your_api_key_here"

# Linux/macOS
export OPENWEATHER_API_KEY="your_api_key_here"
```

---

## 🗄️ MySQL Setup

### Start MySQL Server

Make sure MySQL is running on your machine.

### Manual Setup (Optional)

If you want to create the database manually:

```sql
CREATE DATABASE IF NOT EXISTS weather_pipeline;
USE weather_pipeline;

CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    temperature DECIMAL(5, 2),
    humidity INT,
    weather_condition VARCHAR(50),
    timestamp DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

> **Note:** The pipeline creates the database and table automatically — manual setup is optional.

---

## ▶️ How to Run

### Run Full Pipeline

```bash
python main.py
```

### Run Individual Steps

```bash
python main.py --step 1   # Extract only
python main.py --step 2   # Transform only
python main.py --step 3   # Load only
python main.py --step 4   # Analyze only
```

### Launch Dashboard

```bash
streamlit run dashboard.py
```

### Start Scheduler (Auto-refresh every 30 min)

```bash
python scheduler.py
```

---

## 🔄 Pipeline Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   EXTRACT   │───▶│  TRANSFORM  │───▶│    LOAD     │───▶│   ANALYZE   │
│             │    │             │    │             │    │             │
│ OpenWeather │    │   Pandas    │    │    MySQL    │    │  SQL Queries │
│    API      │    │  Cleaning   │    │  Database   │    │  + Reports  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
  raw_weather      cleaned_weather     weather_data      analysis_
  _data.json       _data.csv           (MySQL table)     results.txt
```

---

## 📊 Sample Output

### Console Output

```
╔══════════════════════════════════════════════════════════════╗
║   🌦️  AUTOMATED ETL PIPELINE — Weather Data                ║
║   Extract  →  Transform  →  Load  →  Analyze               ║
╚══════════════════════════════════════════════════════════════╝

✅ Data Extraction completed in 3.42s
✅ Data Transformation completed in 0.15s
✅ Database Loading completed in 0.28s
✅ SQL Analysis completed in 0.09s

  PIPELINE EXECUTION SUMMARY
  ✅ PASS  Data Extraction
  ✅ PASS  Data Transformation
  ✅ PASS  Database Loading
  ✅ PASS  SQL Analysis
  Total time: 3.94s
  Status: ALL STEPS PASSED ✅
```

### Analysis Report (Sample)

```
======================================================================
  Average Temperature by City
======================================================================
  City        Avg Temp (°C)   Min Temp (°C)   Max Temp (°C)
  ----------------------------------------------------------------
  Dubai       38.50           38.50           38.50
  Mumbai      33.20           33.20           33.20
  Delhi       31.80           31.80           31.80
  Tokyo       22.10           22.10           22.10
  Paris       18.60           18.60           18.60
  London      14.30           14.30           14.30
  Toronto     12.50           12.50           12.50
```

---

## 🔮 Future Improvements

- [ ] Add more data sources (air quality, news sentiment)
- [ ] Implement incremental loading (UPSERT instead of full refresh)
- [ ] Add data validation layer (Great Expectations)
- [ ] Create CI/CD pipeline with GitHub Actions
- [ ] Add unit tests with pytest
- [ ] Migrate to PostgreSQL for production
- [ ] Implement data versioning with DVC
- [ ] Add email/Slack alerts on pipeline failure

---

## 📝 What I Learned

Building this project helped me understand:

1. **ETL fundamentals** — how data moves from source to destination
2. **API integration** — working with REST APIs and handling errors
3. **Data cleaning** — handling missing values, type conversion, deduplication
4. **SQL skills** — writing analytical queries with JOINs, GROUP BY, aggregations
5. **Python best practices** — modular code, logging, error handling
6. **Database design** — creating indexed tables, using parameterized queries
7. **Data visualization** — building dashboards with Streamlit & Plotly

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit PRs.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ as a Data Engineering portfolio project**

⭐ Star this repo if you found it helpful!

</div>
