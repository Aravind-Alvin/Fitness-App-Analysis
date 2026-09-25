"""
Bellabeat Fitness Data Analytics — Streamlit Dashboard
========================================================
Run with:  streamlit run app.py
(requires bellabeat.db in the same folder — built by build_database.py)
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

import bellabeat_analysis as ba

DB_PATH = Path(__file__).parent / "bellabeat.db"

st.set_page_config(
    page_title="Bellabeat Fitness Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

BELLABEAT_GREEN = "#3A6351"

st.markdown(f"""
<style>
    .main-title {{ color:{BELLABEAT_GREEN}; font-size:2.1rem; font-weight:700; margin-bottom:0; }}
    .sub-title {{ color:#666; font-size:1rem; margin-top:0; }}
    div[data-testid="stMetric"] {{
        background-color:#F4F7F4; border-radius:10px; padding:12px 8px; border:1px solid #E1E8E2;
    }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DATA LOADING (cached)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def load_all():
    conn = get_connection()
    return ba.load_tables(conn)


if not DB_PATH.exists():
    st.error(
        "bellabeat.db not found. Run `python build_database.py` first "
        "(it reads the raw CSVs and builds the database this app needs)."
    )
    st.stop()

tables = load_all()
daily_activity = tables["daily_activity"]
hourly_activity = tables["hourly_activity"]
daily_sleep = tables["daily_sleep"]
weight_log = tables["weight_log"]
user_summary = tables["user_summary"]

ALL_USERS = sorted(daily_activity["id"].unique())

# ---------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 🌿 Bellabeat Analytics")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Overview", "🏃 Activity Analysis", "😴 Sleep Analysis",
     "⚖️ Weight & Engagement", "🗄️ SQL Playground", "📋 Findings & Recommendations"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")
selected_users = st.sidebar.multiselect(
    "User ID (Activity & Sleep pages)", ALL_USERS, default=[],
    help="Leave empty to include all 33 users.",
)
if selected_users:
    da_f = daily_activity[daily_activity["id"].isin(selected_users)]
    ha_f = hourly_activity[hourly_activity["id"].isin(selected_users)]
    ds_f = daily_sleep[daily_sleep["id"].isin(selected_users)]
else:
    da_f, ha_f, ds_f = daily_activity, hourly_activity, daily_sleep

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: 33 Fitbit users, self-reported via Amazon Mechanical Turk survey, "
    "Apr 12 – May 12 2016. Used as a proxy for Bellabeat smart-device users."
)


# ---------------------------------------------------------------------------
# PAGE: OVERVIEW
# ---------------------------------------------------------------------------
if page == "🏠 Overview":
    st.markdown('<p class="main-title">STRAVA / Bellabeat Fitness Data Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">How consumers use their smart devices — insights for Bellabeat marketing strategy</p>',
                unsafe_allow_html=True)
    st.markdown("")
    # -----------------------------------------------------------------------
    # KPI CARDS
    # -----------------------------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)
    
c1.markdown(f"""
    <div style="
        background-color: #E8F4FF;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #B8DFFF;
    ">
        <div style="
            color: #0066CC;
            font-size: 16px;
            font-weight: 600;
        ">
            Users Tracked
        </div>
        <div style="
            color: #003366;
            font-size: 28px;
            font-weight: bold;
        ">
            {daily_activity['id'].nunique()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c2.markdown(f"""
    <div style="
        background-color: #EAF7EA;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #B8E0B8;
    ">
        <div style="
            color: #198754;
            font-size: 16px;
            font-weight: 600;
        ">
            Days Covered
        </div>
        <div style="
            color: #146C43;
            font-size: 28px;
            font-weight: bold;
        ">
            {(daily_activity['activity_date'].max() - daily_activity['activity_date'].min()).days + 1}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c3.markdown(f"""
    <div style="
        background-color: #FFF4E5;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #FFD699;
    ">
        <div style="
            color: #E67E00;
            font-size: 16px;
            font-weight: 600;
        ">
            Avg. Daily Steps
        </div>
        <div style="
            color: #A65300;
            font-size: 28px;
            font-weight: bold;
        ">
            {daily_activity['total_steps'].mean():,.0f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c4.markdown(f"""
    <div style="
        background-color: #FCE8F3;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #F3B6D2;
    ">
        <div style="
            color: #C2185B;
            font-size: 16px;
            font-weight: 600;
        ">
            Avg. Sedentary Hours/Day
        </div>
        <div style="
            color: #880E4F;
            font-size: 28px;
            font-weight: bold;
        ">
            {daily_activity['sedentary_minutes'].mean()/60:.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c5.markdown(f"""
    <div style="
        background-color: #F0EAFE;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #D5C5F5;
    ">
        <div style="
            color: #6F42C1;
            font-size: 16px;
            font-weight: 600;
        ">
            Avg. Sleep (hrs)
        </div>
        <div style="
            color: #4B2A85;
            font-size: 28px;
            font-weight: bold;
        ">
            {daily_sleep['total_minutes_asleep'].mean()/60:.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Business Task")
        st.write(
            "Bellabeat's co-founder believes smart-device usage data can reveal growth "
            "opportunities. This dashboard analyzes how people actually use fitness trackers "
            "— activity, sleep, and weight-logging behavior — to inform Bellabeat's marketing "
            "strategy for its **Bellabeat app**, the product that most closely mirrors this data "
            "(it aggregates activity, sleep, and manually-logged weight in one place, just like "
            "these devices do)."
        )
        st.subheader("Data Sources")
        st.write(
            "- `daily_activity` — 940 daily records, 33 users\n"
            "- `hourly_activity` — 22,099 hourly records\n"
            "- `daily_sleep` — 410 nightly records, 24 users\n"
            "- `weight_log` — 67 weigh-ins, 8 users\n"
        )
    with col2:
        st.subheader("Feature Engagement")
        fig = ba.chart_feature_engagement(user_summary)
        st.pyplot(fig, clear_figure=True)

    st.info(
        "Use the sidebar to explore **Activity**, **Sleep**, **Weight & Engagement** analysis, "
        "run your own queries in the **SQL Playground**, or jump to **Findings & Recommendations**.",
        icon="👈",
    )


# ---------------------------------------------------------------------------
# PAGE: ACTIVITY ANALYSIS
# ---------------------------------------------------------------------------
elif page == "🏃 Activity Analysis":
    st.header("🏃 Activity Analysis")
    st.caption(f"Showing {da_f['id'].nunique()} user(s), {len(da_f)} day-records")

    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(ba.chart_steps_distribution(da_f), clear_figure=True)
        st.caption(f"Only **{(da_f['total_steps']>=10000).mean()*100:.0f}%** of days meet the 10,000-step guideline.")
    with col2:
        st.pyplot(ba.chart_activity_minutes_breakdown(da_f), clear_figure=True)
        st.caption("Sedentary time dominates the average day by a wide margin.")

    col3, col4 = st.columns(2)
    with col3:
        st.pyplot(ba.chart_weekday_pattern(da_f), clear_figure=True)
    with col4:
        st.pyplot(ba.chart_hourly_pattern(ha_f), clear_figure=True)
        st.caption("Activity climbs through the day, peaking in the early evening.")

    st.pyplot(ba.chart_steps_vs_calories(da_f), clear_figure=True)
    st.caption(f"Correlation between steps and calories burned: **r = {da_f['total_steps'].corr(da_f['calories']):.2f}**")


# ---------------------------------------------------------------------------
# PAGE: SLEEP ANALYSIS
# ---------------------------------------------------------------------------
elif page == "😴 Sleep Analysis":
    st.header("😴 Sleep Analysis")
    st.caption(f"Showing {ds_f['id'].nunique()} user(s), {len(ds_f)} night-records "
               f"({user_summary['has_sleep_data'].sum()}/{len(user_summary)} users logged sleep at all)")

    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(ba.chart_sleep_distribution(ds_f), clear_figure=True)
        st.metric("Avg. sleep efficiency (asleep ÷ time in bed)", f"{ds_f['sleep_efficiency_pct'].mean():.1f}%")
    with col2:
        st.pyplot(ba.chart_sleep_vs_sedentary(da_f, ds_f), clear_figure=True)
        merged = ba.merge_sleep_activity(da_f, ds_f)
        corr = merged["sedentary_minutes"].corr(merged["total_minutes_asleep"])
        st.caption(f"Sedentary minutes vs. sleep minutes same-day correlation: **r = {corr:.2f}** — "
                   "more sedentary daytime is associated with less sleep that night.")


# ---------------------------------------------------------------------------
# PAGE: WEIGHT & ENGAGEMENT
# ---------------------------------------------------------------------------
elif page == "⚖️ Weight & Engagement":
    st.header("⚖️ Weight Logging & Device Engagement")
    st.warning(
        f"Only **{weight_log['id'].nunique()} of 33 users** ever logged weight, and 5 of those "
        "logged it 2 times or fewer — treat weight findings as directional, not statistically robust.",
        icon="⚠️",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(ba.chart_activity_level_segments(user_summary), clear_figure=True)
    with col2:
        st.pyplot(ba.chart_logging_consistency(user_summary), clear_figure=True)

    st.subheader("Weight Log Detail")
    wl_display = weight_log.merge(
        weight_log.groupby("id").size().rename("n_logs"), on="id"
    ).sort_values(["n_logs", "id"], ascending=[False, True])
    st.dataframe(wl_display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PAGE: SQL PLAYGROUND
# ---------------------------------------------------------------------------
elif page == "🗄️ SQL Playground":
    st.header("🗄️ SQL Playground")
    st.write("Run your own SQL against the cleaned Bellabeat SQLite database. Pick a sample query to start, "
             "edit it, or write your own `SELECT` statement.")

    with st.expander("📖 Database schema", expanded=False):
        conn = get_connection()
        for tbl in ["daily_activity", "hourly_activity", "daily_sleep", "weight_log", "user_summary"]:
            info = pd.read_sql(f"PRAGMA table_info({tbl})", conn)
            st.markdown(f"**`{tbl}`**  ({len(info)} columns)")
            st.dataframe(info[["name", "type"]].T, use_container_width=True, hide_index=False)

    SAMPLE_QUERIES = {
        "-- write your own --": "SELECT * FROM daily_activity LIMIT 10;",
        "Average steps & calories per user": (
            "SELECT id, ROUND(AVG(total_steps),0) AS avg_steps, ROUND(AVG(calories),0) AS avg_calories\n"
            "FROM daily_activity\nGROUP BY id\nORDER BY avg_steps DESC;"
        ),
        "Top 10 most active days (by steps)": (
            "SELECT id, activity_date, total_steps, calories\n"
            "FROM daily_activity\nORDER BY total_steps DESC\nLIMIT 10;"
        ),
        "Activity-level segment counts": (
            "SELECT activity_level, COUNT(*) AS n_users\n"
            "FROM user_summary\nGROUP BY activity_level\nORDER BY n_users DESC;"
        ),
        "Average steps by day of week": (
            "SELECT day_of_week, ROUND(AVG(total_steps),0) AS avg_steps\n"
            "FROM daily_activity\nGROUP BY day_of_week\nORDER BY avg_steps DESC;"
        ),
        "Peak activity hours": (
            "SELECT hour_of_day, ROUND(AVG(step_total),0) AS avg_steps, ROUND(AVG(calories),0) AS avg_calories\n"
            "FROM hourly_activity\nGROUP BY hour_of_day\nORDER BY avg_steps DESC\nLIMIT 5;"
        ),
        "Sleep efficiency by user": (
            "SELECT id, COUNT(*) AS nights_logged, ROUND(AVG(sleep_efficiency_pct),1) AS avg_efficiency\n"
            "FROM daily_sleep\nGROUP BY id\nORDER BY avg_efficiency DESC;"
        ),
        "Weight log frequency per user": (
            "SELECT id, COUNT(*) AS n_logs, ROUND(AVG(weight_kg),1) AS avg_weight_kg\n"
            "FROM weight_log\nGROUP BY id\nORDER BY n_logs DESC;"
        ),
        "Users who log sleep AND weight": (
            "SELECT id, days_logged_activity, has_sleep_data, has_weight_data, activity_level\n"
            "FROM user_summary\nWHERE has_sleep_data = 1 AND has_weight_data = 1;"
        ),
    }

    choice = st.selectbox("Sample queries", list(SAMPLE_QUERIES.keys()))
    query = st.text_area("SQL query", value=SAMPLE_QUERIES[choice], height=140)

    run_col, dl_col = st.columns([1, 5])
    run = run_col.button("▶️ Run Query", type="primary")

    if run:
        if not query.strip().lower().startswith("select") and not query.strip().lower().startswith("pragma"):
            st.error("Only SELECT / PRAGMA statements are allowed in this playground.")
        else:
            try:
                conn = get_connection()
                result = pd.read_sql_query(query, conn)
                st.success(f"{len(result)} row(s) returned")
                st.dataframe(result, use_container_width=True)

                csv = result.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download results as CSV", csv, "query_results.csv", "text/csv")

                numeric_cols = result.select_dtypes("number").columns
                if len(result) > 1 and len(numeric_cols) >= 1 and result.shape[1] >= 2:
                    st.markdown("**Quick chart** (first text column as category, first numeric column as value)")
                    non_numeric = [c for c in result.columns if c not in numeric_cols]
                    if non_numeric:
                        st.bar_chart(result.set_index(non_numeric[0])[numeric_cols[0]])
            except Exception as e:
                st.error(f"Query failed: {e}")


# ---------------------------------------------------------------------------
# PAGE: FINDINGS & RECOMMENDATIONS
# ---------------------------------------------------------------------------
else:
    st.header("📋 Key Findings & Recommendations")

    _sleep_act_merged = ba.merge_sleep_activity(daily_activity, daily_sleep)
    _sleep_sed_corr = _sleep_act_merged["sedentary_minutes"].corr(_sleep_act_merged["total_minutes_asleep"])

    st.subheader("Key Findings")
    st.markdown(f"""
1. **Sedentary time dominates the day.** Users average **{daily_activity['sedentary_minutes'].mean()/60:.1f} hours/day**
   sedentary versus only **{daily_activity['very_active_minutes'].mean():.0f} minutes/day** very active — owning a
   tracker doesn't by itself change behavior.
2. **Most users fall short of the 10,000-step benchmark.** Only **{(daily_activity['total_steps']>=10000).mean()*100:.0f}%**
   of day-records hit 10k steps; **{(user_summary['activity_level'].isin(['Sedentary','Low Active'])).mean()*100:.0f}%**
   of users average "Sedentary" or "Low Active" step counts.
3. **Weekday and weekend activity are nearly identical**, suggesting steps come mostly from routine
   (commuting, work) rather than deliberate exercise — leisure-time activity isn't being captured or encouraged.
4. **Activity peaks in the early evening** (around 6 PM), a natural window for reminders or workout prompts.
5. **Sleep tracking has strong adoption** ({user_summary['has_sleep_data'].mean()*100:.0f}% of users) with healthy average
   sleep efficiency ({daily_sleep['sleep_efficiency_pct'].mean():.0f}%), and more sedentary days are correlated with
   *less* sleep that night (r = {_sleep_sed_corr:.2f}).
6. **Weight logging is the weakest feature.** Only **{user_summary['has_weight_data'].mean()*100:.0f}%** of users ever logged
   weight, and most who tried it stopped after 1-2 entries — manual weight entry is high-friction.
""")

    st.subheader("Top Recommendations for Bellabeat Marketing")
    st.markdown("""
1. **Lead marketing with "close the sedentary gap," not just step counts.** Position the Bellabeat app around
   hourly move reminders and reducing sitting time — a message the data shows is genuinely under-addressed.
2. **Personalize goals instead of a single 10k-step target.** Segment users (Sedentary → Highly Active) and market
   tiered, achievable step goals with in-app celebration of tier-ups to drive habit formation.
3. **Promote evening engagement windows.** Time push notifications, challenges, and social features around the
   5–7 PM activity peak, when users are already primed to move.
4. **Cross-sell sleep and activity as one story.** Since sedentary time predicts worse sleep, market the app's
   combined sleep + activity insight as a differentiator over single-purpose trackers.
5. **Fix or de-emphasize manual weight logging.** Either pair the app with a connected smart scale (auto-sync,
   zero manual entry) or reduce weight's prominence in marketing until friction is resolved — right now it under-delivers.
6. **Target weekend-specific campaigns.** Since weekend activity doesn't naturally rise, run weekend challenges
   or social step competitions to convert leisure time into activity, an opportunity competitors aren't capturing.
""")

    st.caption("Full documentation of data sources, cleaning steps, and methodology is in the accompanying Word report.")
