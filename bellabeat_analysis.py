"""
bellabeat_analysis.py
----------------------
Shared data-loading and chart-building functions for the Bellabeat Fitness
Data Analytics project. Imported by both:
  - generate_report_assets.py  (renders static PNGs for the Word report)
  - app.py                     (renders the same charts live in Streamlit)

Keeping this logic in one module means the report and the app always show
identical analysis.
"""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", palette="viridis")
BELLABEAT_PALETTE = ["#3A6351", "#7CA982", "#B4CFB0", "#E1B07E", "#D46A6A"]


def get_connection(db_path="bellabeat.db"):
    return sqlite3.connect(db_path)


def load_tables(conn):
    tables = {}
    for name in ["daily_activity", "hourly_activity", "daily_sleep", "weight_log", "user_summary"]:
        tables[name] = pd.read_sql(f"SELECT * FROM {name}", conn)
    tables["daily_activity"]["activity_date"] = pd.to_datetime(tables["daily_activity"]["activity_date"])
    tables["daily_sleep"]["sleep_date"] = pd.to_datetime(tables["daily_sleep"]["sleep_date"])
    tables["weight_log"]["log_date"] = pd.to_datetime(tables["weight_log"]["log_date"])
    tables["hourly_activity"]["activity_hour"] = pd.to_datetime(tables["hourly_activity"]["activity_hour"])

    # SQLite has no native boolean type -> these round-trip as 0/1 integers; cast back to bool
    tables["daily_activity"]["is_weekend"] = tables["daily_activity"]["is_weekend"].astype(bool)
    tables["daily_activity"]["is_zero_step_day"] = tables["daily_activity"]["is_zero_step_day"].astype(bool)
    tables["weight_log"]["is_manual_report"] = tables["weight_log"]["is_manual_report"].astype(bool)
    tables["user_summary"]["has_sleep_data"] = tables["user_summary"]["has_sleep_data"].astype(bool)
    tables["user_summary"]["has_weight_data"] = tables["user_summary"]["has_weight_data"].astype(bool)
    return tables


# ---------------------------------------------------------------------------
# CHART FUNCTIONS — each takes cleaned dataframes and returns a matplotlib Figure
# ---------------------------------------------------------------------------

def chart_steps_distribution(daily_activity):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.histplot(daily_activity["total_steps"], bins=30, color=BELLABEAT_PALETTE[0], ax=ax)
    ax.axvline(10000, color=BELLABEAT_PALETTE[4], linestyle="--", linewidth=2, label="10,000-step guideline")
    ax.set_title("Distribution of Daily Steps Across All Users")
    ax.set_xlabel("Total Steps in a Day")
    ax.set_ylabel("Number of Day-Records")
    ax.legend()
    fig.tight_layout()
    return fig


def chart_activity_minutes_breakdown(daily_activity):
    means = daily_activity[[
        "sedentary_minutes", "lightly_active_minutes", "fairly_active_minutes", "very_active_minutes"
    ]].mean()
    labels = ["Sedentary", "Lightly Active", "Fairly Active", "Very Active"]
    total = means.sum()

    fig, ax = plt.subplots(figsize=(8, 4.5))

    def autopct_fmt(pct):
        return f"{pct:.0f}%" if pct >= 4 else ""

    wedges, _texts, _autotexts = ax.pie(
        means, colors=BELLABEAT_PALETTE[:4], autopct=autopct_fmt, startangle=90, pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    legend_labels = [f"{l}: {m:.0f} min ({m/total*100:.0f}%)" for l, m in zip(labels, means)]
    ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, fontsize=10)
    ax.set_title("Average Minutes Per Day by Activity Intensity")
    fig.tight_layout()
    return fig


def chart_steps_vs_calories(daily_activity):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.regplot(data=daily_activity, x="total_steps", y="calories", ax=ax,
                scatter_kws={"alpha": 0.35, "color": BELLABEAT_PALETTE[0]},
                line_kws={"color": BELLABEAT_PALETTE[4]})
    ax.set_title("Daily Steps vs. Calories Burned")
    ax.set_xlabel("Total Steps")
    ax.set_ylabel("Calories Burned")
    fig.tight_layout()
    return fig


def chart_weekday_pattern(daily_activity):
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grp = daily_activity.groupby("day_of_week")["total_steps"].mean().reindex(order)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = [BELLABEAT_PALETTE[4] if d in ("Saturday", "Sunday") else BELLABEAT_PALETTE[0] for d in order]
    sns.barplot(x=grp.index, y=grp.values, hue=grp.index, palette=colors, legend=False, ax=ax)
    ax.set_title("Average Daily Steps by Day of Week")
    ax.set_xlabel("")
    ax.set_ylabel("Average Steps")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig


def chart_hourly_pattern(hourly_activity):
    grp = hourly_activity.groupby("hour_of_day")[["step_total", "calories"]].mean()
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax2 = ax.twinx()
    ax.bar(grp.index, grp["step_total"], color=BELLABEAT_PALETTE[1], alpha=0.7, label="Avg. Steps")
    ax2.plot(grp.index, grp["calories"], color=BELLABEAT_PALETTE[4], linewidth=2.5, marker="o",
             markersize=4, label="Avg. Calories")
    ax.set_title("Average Steps & Calories by Hour of Day")
    ax.set_xlabel("Hour of Day (0-23)")
    ax.set_ylabel("Average Steps", color=BELLABEAT_PALETTE[1])
    ax2.set_ylabel("Average Calories", color=BELLABEAT_PALETTE[4])
    ax.set_xticks(range(0, 24, 2))
    fig.tight_layout()
    return fig


def chart_sleep_distribution(daily_sleep):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.histplot(daily_sleep["total_minutes_asleep"] / 60, bins=24, color=BELLABEAT_PALETTE[2], ax=ax)
    ax.axvline(7, color=BELLABEAT_PALETTE[4], linestyle="--", linewidth=2, label="7-hour guideline")
    ax.set_title("Distribution of Nightly Sleep Duration")
    ax.set_xlabel("Hours Asleep")
    ax.set_ylabel("Number of Night-Records")
    ax.legend()
    fig.tight_layout()
    return fig


def merge_sleep_activity(daily_activity, daily_sleep):
    """One row per user-day that has BOTH an activity record and a sleep record."""
    return pd.merge(
        daily_activity[["id", "activity_date", "sedentary_minutes", "total_steps"]],
        daily_sleep[["id", "sleep_date", "total_minutes_asleep"]],
        left_on=["id", "activity_date"], right_on=["id", "sleep_date"],
    )


def chart_sleep_vs_sedentary(daily_activity, daily_sleep):
    merged = merge_sleep_activity(daily_activity, daily_sleep)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.regplot(data=merged, x="sedentary_minutes", y="total_minutes_asleep", ax=ax,
                scatter_kws={"alpha": 0.4, "color": BELLABEAT_PALETTE[0]},
                line_kws={"color": BELLABEAT_PALETTE[4]})
    ax.set_title("Sedentary Minutes vs. Minutes Asleep (same day)")
    ax.set_xlabel("Sedentary Minutes")
    ax.set_ylabel("Minutes Asleep")
    fig.tight_layout()
    return fig


def chart_activity_level_segments(user_summary):
    order = ["Sedentary", "Low Active", "Somewhat Active", "Active", "Highly Active"]
    counts = user_summary["activity_level"].value_counts().reindex(order).fillna(0)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.barplot(x=counts.index, y=counts.values, hue=counts.index,
                palette=BELLABEAT_PALETTE[: len(counts)], legend=False, ax=ax)
    ax.set_title("Users by Activity-Level Segment (based on avg. daily steps)")
    ax.set_xlabel("")
    ax.set_ylabel("Number of Users")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    return fig


def chart_feature_engagement(user_summary):
    total = len(user_summary)
    feature_counts = {
        "Logged\nActivity": total,
        "Logged\nSleep": user_summary["has_sleep_data"].sum(),
        "Logged\nWeight": user_summary["has_weight_data"].sum(),
    }
    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(feature_counts.keys(), feature_counts.values(), color=BELLABEAT_PALETTE[:3])
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 0.5, f"{int(h)}/{total}", ha="center", fontweight="bold")
    ax.set_title("Feature Engagement Across 33 Users")
    ax.set_ylabel("Number of Users")
    ax.set_ylim(0, total + 4)
    fig.tight_layout()
    return fig


def chart_logging_consistency(user_summary, total_days=31):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    pct = (user_summary["days_logged_activity"] / total_days * 100).sort_values(ascending=False)
    sns.barplot(x=list(range(1, len(pct) + 1)), y=pct.values, hue=list(range(1, len(pct) + 1)),
                palette="viridis", legend=False, ax=ax)
    ax.set_title("Device Logging Consistency by User\n(% of the ~31-day window with an activity record)")
    ax.set_xlabel("Users (ranked)")
    ax.set_ylabel("% of Days Logged")
    ax.set_xticks([])
    fig.tight_layout()
    return fig
