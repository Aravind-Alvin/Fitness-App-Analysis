"""
generate_report_assets.py
--------------------------
Runs once to (1) render every chart as a PNG for the Word report, and
(2) print/save the key summary statistics referenced in the report text,
so every number quoted in the report is generated directly from the data.
"""
import json
from pathlib import Path

import bellabeat_analysis as ba

OUT = Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

conn = ba.get_connection(str(Path(__file__).parent / "bellabeat.db"))
t = ba.load_tables(conn)
da, ha, ds, wl, us = t["daily_activity"], t["hourly_activity"], t["daily_sleep"], t["weight_log"], t["user_summary"]

charts = {
    "steps_distribution.png": ba.chart_steps_distribution(da),
    "activity_minutes_breakdown.png": ba.chart_activity_minutes_breakdown(da),
    "steps_vs_calories.png": ba.chart_steps_vs_calories(da),
    "weekday_pattern.png": ba.chart_weekday_pattern(da),
    "hourly_pattern.png": ba.chart_hourly_pattern(ha),
    "sleep_distribution.png": ba.chart_sleep_distribution(ds),
    "activity_level_segments.png": ba.chart_activity_level_segments(us),
    "feature_engagement.png": ba.chart_feature_engagement(us),
    "logging_consistency.png": ba.chart_logging_consistency(us),
}
fig_sleep_sed = ba.chart_sleep_vs_sedentary(da, ds)
merged_sleep_sed = ba.merge_sleep_activity(da, ds)
charts["sleep_vs_sedentary.png"] = fig_sleep_sed

for fname, fig in charts.items():
    fig.savefig(OUT / fname, dpi=150, bbox_inches="tight")
    print("saved", fname)

# ---------------------------------------------------------------------------
# Key stats used verbatim in the report text
# ---------------------------------------------------------------------------
stats = {}
stats["n_users_activity"] = int(da["id"].nunique())
stats["n_users_sleep"] = int(ds["id"].nunique())
stats["n_users_weight"] = int(wl["id"].nunique())
stats["date_min"] = str(da["activity_date"].min().date())
stats["date_max"] = str(da["activity_date"].max().date())
stats["total_days_span"] = int((da["activity_date"].max() - da["activity_date"].min()).days + 1)

stats["avg_steps"] = round(da["total_steps"].mean(), 0)
stats["pct_meeting_10k"] = round((da["total_steps"] >= 10000).mean() * 100, 1)
stats["pct_zero_step_days"] = round((da["total_steps"] == 0).mean() * 100, 1)

stats["avg_sedentary_minutes"] = round(da["sedentary_minutes"].mean(), 0)
stats["avg_sedentary_hours"] = round(da["sedentary_minutes"].mean() / 60, 1)
stats["avg_very_active_minutes"] = round(da["very_active_minutes"].mean(), 1)
stats["avg_lightly_active_minutes"] = round(da["lightly_active_minutes"].mean(), 1)

stats["steps_calories_corr"] = round(da["total_steps"].corr(da["calories"]), 2)

weekday_steps = da[~da["is_weekend"]]["total_steps"].mean()
weekend_steps = da[da["is_weekend"]]["total_steps"].mean()
stats["weekday_avg_steps"] = round(weekday_steps, 0)
stats["weekend_avg_steps"] = round(weekend_steps, 0)
stats["weekend_vs_weekday_pct_diff"] = round((weekend_steps - weekday_steps) / weekday_steps * 100, 1)

peak_hour = ha.groupby("hour_of_day")["step_total"].mean().idxmax()
stats["peak_activity_hour"] = int(peak_hour)

stats["avg_sleep_minutes"] = round(ds["total_minutes_asleep"].mean(), 0)
stats["avg_sleep_hours"] = round(ds["total_minutes_asleep"].mean() / 60, 1)
stats["avg_sleep_efficiency"] = round(ds["sleep_efficiency_pct"].mean(), 1)
stats["sleep_sedentary_corr"] = round(
    merged_sleep_sed["sedentary_minutes"].corr(merged_sleep_sed["total_minutes_asleep"]), 2
)

stats["pct_users_logged_sleep"] = round(us["has_sleep_data"].mean() * 100, 1)
stats["pct_users_logged_weight"] = round(us["has_weight_data"].mean() * 100, 1)
stats["max_days_logged_activity"] = int(us["days_logged_activity"].max())
stats["min_days_logged_activity"] = int(us["days_logged_activity"].min())
stats["avg_days_logged_activity"] = round(us["days_logged_activity"].mean(), 1)

stats["activity_level_counts"] = us["activity_level"].value_counts().to_dict()

weight_counts = wl["id"].value_counts()
stats["weight_power_users"] = int((weight_counts >= 10).sum())
stats["weight_one_time_users"] = int((weight_counts <= 2).sum())

with open(Path(__file__).parent / "report_stats.json", "w") as f:
    json.dump(stats, f, indent=2, default=str)

print(json.dumps(stats, indent=2, default=str))
conn.close()
