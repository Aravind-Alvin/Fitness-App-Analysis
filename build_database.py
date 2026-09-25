"""
build_database.py
------------------
Bellabeat Fitness Data Analytics — Data Cleaning & SQLite Build Script

Reads the raw Fitbit/Bellabeat CSV exports, cleans them, and writes a single
SQLite database (bellabeat.db) with five analysis-ready tables:

    daily_activity   - one row per user per day: steps, distance, activity
                        minutes by intensity, calories
    hourly_activity  - one row per user per hour: steps, calories, intensity
    daily_sleep      - one row per user per day: sleep records/minutes
    weight_log       - one row per user per weigh-in: weight, BMI
    user_summary      - one row per user: engagement + behavioral summary
                        (used heavily by the Streamlit app & SQL playground)

Run once:  python build_database.py
Produces:  bellabeat.db
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path("/mnt/user-data/uploads")
DB_PATH = Path(__file__).parent / "bellabeat.db"

CLEANING_LOG = []


def log(msg):
    print(msg)
    CLEANING_LOG.append(msg)


# ---------------------------------------------------------------------------
# 1. DAILY ACTIVITY
# ---------------------------------------------------------------------------
def build_daily_activity():
    df = pd.read_csv(RAW_DIR / "dailyActivity_merged.csv")
    log(f"[daily_activity] loaded {len(df)} raw rows, {df['Id'].nunique()} users")

    # dailyCalories_merged / dailyIntensities_merged / dailySteps_merged are
    # verified exact subsets of dailyActivity_merged -> not loaded separately
    # (avoids redundant tables; verified with a value-level equality check).

    df = df.drop_duplicates()
    dup_dropped = len(df)
    df["Id"] = df["Id"].astype(str)
    df["activity_date"] = pd.to_datetime(df["ActivityDate"], format="%m/%d/%Y")

    df = df.rename(columns={
        "TotalSteps": "total_steps",
        "TotalDistance": "total_distance",
        "TrackerDistance": "tracker_distance",
        "LoggedActivitiesDistance": "logged_activities_distance",
        "VeryActiveDistance": "very_active_distance",
        "ModeratelyActiveDistance": "moderately_active_distance",
        "LightActiveDistance": "light_active_distance",
        "SedentaryActiveDistance": "sedentary_active_distance",
        "VeryActiveMinutes": "very_active_minutes",
        "FairlyActiveMinutes": "fairly_active_minutes",
        "LightlyActiveMinutes": "lightly_active_minutes",
        "SedentaryMinutes": "sedentary_minutes",
        "Calories": "calories",
    })

    df["day_of_week"] = df["activity_date"].dt.day_name()
    df["is_weekend"] = df["activity_date"].dt.dayofweek >= 5
    df["total_active_minutes"] = (
        df["very_active_minutes"] + df["fairly_active_minutes"] + df["lightly_active_minutes"]
    )
    df["is_zero_step_day"] = df["total_steps"] == 0

    keep_cols = [
        "Id", "activity_date", "day_of_week", "is_weekend",
        "total_steps", "total_distance", "tracker_distance", "logged_activities_distance",
        "very_active_distance", "moderately_active_distance", "light_active_distance",
        "sedentary_active_distance", "very_active_minutes", "fairly_active_minutes",
        "lightly_active_minutes", "sedentary_minutes", "total_active_minutes",
        "calories", "is_zero_step_day",
    ]
    df = df[keep_cols].rename(columns={"Id": "id"})
    log(f"[daily_activity] cleaned to {len(df)} rows "
        f"({df['is_zero_step_day'].sum()} zero-step days flagged, not dropped)")
    return df


# ---------------------------------------------------------------------------
# 2. HOURLY ACTIVITY (merge calories + intensities + steps)
# ---------------------------------------------------------------------------
def build_hourly_activity():
    cal = pd.read_csv(RAW_DIR / "hourlyCalories_merged.csv")
    inten = pd.read_csv(RAW_DIR / "hourlyIntensities_merged.csv")
    steps = pd.read_csv(RAW_DIR / "hourlySteps_merged.csv")

    for d in (cal, inten, steps):
        d["Id"] = d["Id"].astype(str)
        d["ActivityHour"] = pd.to_datetime(d["ActivityHour"], format="%m/%d/%Y %I:%M:%S %p")

    merged = cal.merge(inten, on=["Id", "ActivityHour"]).merge(steps, on=["Id", "ActivityHour"])
    merged = merged.drop_duplicates()
    log(f"[hourly_activity] merged calories+intensities+steps -> {len(merged)} rows")

    merged = merged.rename(columns={
        "Id": "id",
        "ActivityHour": "activity_hour",
        "Calories": "calories",
        "TotalIntensity": "total_intensity",
        "AverageIntensity": "average_intensity",
        "StepTotal": "step_total",
    })
    merged["hour_of_day"] = merged["activity_hour"].dt.hour
    merged["activity_date"] = merged["activity_hour"].dt.date.astype(str)
    return merged


# ---------------------------------------------------------------------------
# 3. DAILY SLEEP
# ---------------------------------------------------------------------------
def build_daily_sleep():
    df = pd.read_csv(RAW_DIR / "sleepDay_merged.csv")
    before = len(df)
    df = df.drop_duplicates()
    log(f"[daily_sleep] loaded {before} rows, dropped {before - len(df)} exact duplicate rows")

    df["Id"] = df["Id"].astype(str)
    df["sleep_date"] = pd.to_datetime(df["SleepDay"], format="%m/%d/%Y %I:%M:%S %p").dt.date

    df = df.rename(columns={
        "TotalSleepRecords": "total_sleep_records",
        "TotalMinutesAsleep": "total_minutes_asleep",
        "TotalTimeInBed": "total_time_in_bed",
    })
    df["sleep_efficiency_pct"] = (
        df["total_minutes_asleep"] / df["total_time_in_bed"] * 100
    ).round(1)

    keep = ["Id", "sleep_date", "total_sleep_records", "total_minutes_asleep",
            "total_time_in_bed", "sleep_efficiency_pct"]
    df = df[keep].rename(columns={"Id": "id"})
    log(f"[daily_sleep] cleaned to {len(df)} rows, {df['id'].nunique()} users")
    return df


# ---------------------------------------------------------------------------
# 4. WEIGHT LOG
# ---------------------------------------------------------------------------
def build_weight_log():
    df = pd.read_csv(RAW_DIR / "weightLogInfo_merged.csv")
    log(f"[weight_log] loaded {len(df)} rows, {df['Id'].nunique()} users "
        f"(Fat recorded for only {df['Fat'].notna().sum()} rows -> column dropped)")

    df["Id"] = df["Id"].astype(str)
    df["log_datetime"] = pd.to_datetime(df["Date"], format="%m/%d/%Y %I:%M:%S %p")
    df["log_date"] = df["log_datetime"].dt.date

    df = df.rename(columns={
        "WeightKg": "weight_kg",
        "WeightPounds": "weight_pounds",
        "BMI": "bmi",
        "IsManualReport": "is_manual_report",
    })
    keep = ["Id", "log_date", "weight_kg", "weight_pounds", "bmi", "is_manual_report"]
    df = df[keep].rename(columns={"Id": "id"})
    return df


# ---------------------------------------------------------------------------
# 5. USER SUMMARY (derived engagement + behavior table)
# ---------------------------------------------------------------------------
def build_user_summary(daily_activity, daily_sleep, weight_log):
    n_days_tracked = daily_activity.groupby("id")["activity_date"].nunique().rename("days_logged_activity")

    agg = daily_activity.groupby("id").agg(
        avg_steps=("total_steps", "mean"),
        avg_calories=("calories", "mean"),
        avg_sedentary_minutes=("sedentary_minutes", "mean"),
        avg_very_active_minutes=("very_active_minutes", "mean"),
        avg_fairly_active_minutes=("fairly_active_minutes", "mean"),
        avg_lightly_active_minutes=("lightly_active_minutes", "mean"),
        pct_zero_step_days=("is_zero_step_day", "mean"),
    ).round(1)
    agg["pct_zero_step_days"] = (agg["pct_zero_step_days"] * 100).round(1)

    summary = agg.join(n_days_tracked)

    sleep_agg = daily_sleep.groupby("id").agg(
        days_logged_sleep=("sleep_date", "nunique"),
        avg_minutes_asleep=("total_minutes_asleep", "mean"),
        avg_sleep_efficiency=("sleep_efficiency_pct", "mean"),
    ).round(1)
    summary = summary.join(sleep_agg, how="left")
    summary["has_sleep_data"] = summary["days_logged_sleep"].notna()
    summary[["days_logged_sleep", "avg_minutes_asleep", "avg_sleep_efficiency"]] = (
        summary[["days_logged_sleep", "avg_minutes_asleep", "avg_sleep_efficiency"]].fillna(0)
    )

    weight_agg = weight_log.groupby("id").agg(
        days_logged_weight=("log_date", "nunique"),
    )
    summary = summary.join(weight_agg, how="left")
    summary["has_weight_data"] = summary["days_logged_weight"].notna()
    summary["days_logged_weight"] = summary["days_logged_weight"].fillna(0).astype(int)

    # CDC-style step-count activity segmentation (standard thresholds)
    def classify(steps):
        if steps < 5000:
            return "Sedentary"
        elif steps < 7500:
            return "Low Active"
        elif steps < 10000:
            return "Somewhat Active"
        elif steps < 12500:
            return "Active"
        else:
            return "Highly Active"

    summary["activity_level"] = summary["avg_steps"].apply(classify)
    summary = summary.reset_index()
    log(f"[user_summary] built summary for {len(summary)} users")
    return summary


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    daily_activity = build_daily_activity()
    hourly_activity = build_hourly_activity()
    daily_sleep = build_daily_sleep()
    weight_log = build_weight_log()
    user_summary = build_user_summary(daily_activity, daily_sleep, weight_log)

    # sqlite doesn't have a native date type -> store as ISO text
    daily_activity["activity_date"] = daily_activity["activity_date"].astype(str)
    daily_sleep["sleep_date"] = daily_sleep["sleep_date"].astype(str)
    weight_log["log_date"] = weight_log["log_date"].astype(str)
    hourly_activity["activity_hour"] = hourly_activity["activity_hour"].astype(str)

    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    daily_activity.to_sql("daily_activity", conn, index=False)
    hourly_activity.to_sql("hourly_activity", conn, index=False)
    daily_sleep.to_sql("daily_sleep", conn, index=False)
    weight_log.to_sql("weight_log", conn, index=False)
    user_summary.to_sql("user_summary", conn, index=False)

    for tbl in ["daily_activity", "hourly_activity", "daily_sleep", "weight_log", "user_summary"]:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{tbl}_id ON {tbl}(id)")
    conn.commit()

    log("\n--- ROW COUNTS ---")
    for tbl in ["daily_activity", "hourly_activity", "daily_sleep", "weight_log", "user_summary"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        log(f"{tbl}: {n} rows")
    conn.close()

    with open(Path(__file__).parent / "cleaning_log.txt", "w") as f:
        f.write("\n".join(CLEANING_LOG))

    print(f"\nDatabase written to {DB_PATH}")


if __name__ == "__main__":
    main()
