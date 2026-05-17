-- Weather Pipeline — Database & Table Setup
CREATE DATABASE IF NOT EXISTS weather_pipeline;
USE weather_pipeline;

CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
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
    country VARCHAR(10),
    temp_category VARCHAR(20),
    timestamp DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city (city),
    INDEX idx_timestamp (timestamp),
    INDEX idx_weather (weather_condition)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
