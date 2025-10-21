# AQI-Alert
Uses python libraries to scrape air quality data from major cities in California and send daily reports when it is particularly poor.

> **Mission:** Deliver clear, daily insights into wildfire-related air quality.  
> This system automatically collects air quality data, stores it locally, and emails a single daily digest summarizing air conditions across major California cities.

---

## ✨ Features

- 🕒 **Automated Hourly Data Ingestion**  
  Pulls live PM2.5 readings from [AirNow](https://www.airnow.gov/) every hour and stores them in a local SQLite database.

- ☀️ **Daily 7:05 AM PT Morning Digest**  
  A single HTML email summarizing:
  - The most recent PM2.5 values and EPA category for each city  
  - Yesterday’s **max** and **average** PM2.5  
  - How far each city is above or below the 35 µg/m³ threshold

- 📊 **Local Data Storage**  
  All readings, alerts, and summaries are stored in `aqi.db` for offline analysis.

- 📬 **Email Delivery via Gmail SMTP**  
  Uses secure App Passwords and `.env` configuration for safety.

- 🔒 **Privacy-Friendly & Extensible**  
  No third-party telemetry. Add new data providers (e.g., OpenAQ) or visualization dashboards easily.

---

## 🏗️ Project Architecture

# 🌲 Wildfire AQI Notifier

> **Mission:** Deliver clear, daily insights into wildfire-related air quality.  
> This system automatically collects air quality data, stores it locally, and emails a single daily digest summarizing air conditions across major California cities.

---

## ✨ Features

- 🕒 **Automated Hourly Data Ingestion**  
  Pulls live PM2.5 readings from [AirNow](https://www.airnow.gov/) every hour and stores them in a local SQLite database.

- ☀️ **Daily 7:05 AM PT Morning Digest**  
  A single HTML email summarizing:
  - The most recent PM2.5 values and EPA category for each city  
  - Yesterday’s **max** and **average** PM2.5  
  - How far each city is above or below the 35 µg/m³ threshold

- 📊 **Local Data Storage**  
  All readings, alerts, and summaries are stored in `aqi.db` for offline analysis.

- 📬 **Email Delivery via Gmail SMTP**  
  Uses secure App Passwords and `.env` configuration for safety.

- 🔒 **Privacy-Friendly & Extensible**  
  No third-party telemetry. Add new data providers (e.g., OpenAQ) or visualization dashboards easily.

---

## 🏗️ Project Architecture

wildfire-aqi-notifier/
├─ src/
│ ├─ cli.py # Typer CLI commands
│ ├─ runner.py # Orchestration (ingest, digest)
│ ├─ config.py, db.py, models.py
│ ├─ ingest/ # AirNow API integration
│ ├─ logic/ # Reporting & evaluation logic
│ └─ notify/ # Email notifier
│
├─ config.yaml
├─ requirements.txt
├─ .env.example # Example configuration
└─ README.md
