-- Automated ETL Pipeline — Normalized Relational Database Schema Setup
-- Creating database if not exists (MySQL only)
CREATE DATABASE IF NOT EXISTS weather_pipeline;
USE weather_pipeline;

-- 1. Dimension table for Cities
CREATE TABLE IF NOT EXISTS dim_cities (
    city_id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Fact table for Weather Measurements (includes complementary Air Quality & Forecast data)
CREATE TABLE IF NOT EXISTS fact_weather_measurements (
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
    aqi INT,
    pm2_5 DECIMAL(5, 2),
    pm10 DECIMAL(5, 2),
    forecast_wind_speed DECIMAL(5, 2),
    forecast_humidity INT,
    temp_category VARCHAR(20),
    timestamp DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city_id) REFERENCES dim_cities(city_id),
    UNIQUE KEY uq_city_timestamp (city_id, timestamp),
    INDEX idx_city_id (city_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_weather (weather_condition)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
