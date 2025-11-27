# Ad Revenue ETL Pipeline

A simple Python ETL pipeline that processes ad performance data (impressions, clicks, revenue) and generates daily campaign metrics.

## Features
- Loads raw CSV files (impressions, clicks, revenue)
- Cleans and merges datasets using Pandas
- Calculates CTR, RPM, and revenue (CAD normalized)
- Aggregates metrics by date and campaign
- Saves results to SQLite and exports CSV reports

## Tech Stack
- Python
- Pandas
- SQLite
- CSV

## Project Structure
ad-revenue-pipeline/
data/raw/
reports/
pipeline.py

shell
Copy code

## How to Run
python pipeline.py

markdown
Copy code

## Output
- `ads_analytics.db` (auto-generated)
- `reports/...csv` (timestamped analytics report)
