# Bellabeat Fitness Data Analytics

A Streamlit dashboard + SQL playground built on the Fitbit smart-device dataset,
analyzed as a proxy for how Bellabeat customers use their smart devices.

## What's in this folder

| File | Purpose |
|---|---|
| `build_database.py` | Cleans the raw CSVs and builds `bellabeat.db` (SQLite). Already run once — `bellabeat.db` is included, so you don't need the raw CSVs to use the app. |
| `bellabeat_analysis.py` | Shared data-loading + chart functions (matplotlib/seaborn), used by both the app and the report generator. |
| `generate_report_assets.py` | Regenerates the chart PNGs and summary statistics used in the Word report. |
| `app.py` | The Streamlit dashboard — **this is what you run**. |
| `bellabeat.db` | The cleaned SQLite database (5 tables) that powers both the dashboard and the SQL playground. |
| `cleaning_log.txt` | Plain-text log of every cleaning step applied to the raw data. |
| `report_stats.json` | Every summary statistic quoted in the Word report, computed directly from the data. |
| `charts/` | Static PNG versions of every chart (used in the Word report). |

## How to run the dashboard

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will open the dashboard in your browser (usually `http://localhost:8501`).

## Dashboard pages

- **Overview** — KPIs and business context
- **Activity Analysis** — steps, intensity minutes, weekday/hourly patterns, steps-vs-calories
- **Sleep Analysis** — sleep duration, efficiency, sleep-vs-sedentary relationship
- **Weight & Engagement** — weight-logging behavior, activity-level segments, logging consistency
- **SQL Playground** — write and run your own SQL against `bellabeat.db`, with sample queries, a schema browser, and CSV export
- **Findings & Recommendations** — the headline takeaways and marketing recommendations, generated live from the current data

## Rebuilding from scratch (optional)

If you want to regenerate everything from the original raw CSVs:

```bash
# 1. Place the raw Fitbit CSVs in the same folder as build_database.py,
#    or edit RAW_DIR at the top of build_database.py to point to them.
python build_database.py            # rebuilds bellabeat.db
python generate_report_assets.py    # regenerates charts/ and report_stats.json
```

## Database schema (SQLite)

- **daily_activity** — one row per user/day: steps, distance, activity minutes by intensity, calories
- **hourly_activity** — one row per user/hour: steps, calories, intensity
- **daily_sleep** — one row per user/night: sleep records, minutes asleep, time in bed, sleep efficiency
- **weight_log** — one row per weigh-in: weight (kg/lb), BMI, manual vs. auto report
- **user_summary** — one row per user: engagement + behavior summary (days logged, averages, activity-level segment) — built for fast SQL playground queries
