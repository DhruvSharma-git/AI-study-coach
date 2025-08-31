import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import datetime
import random

# --- DATABASE CONNECTION ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('study_companion.db')
    return conn

# --- AI-POWERED INSIGHTS ---
def generate_ai_insight(df_mood, df_habits, df_completions):
    """Generates a personalized insight based on mood and habit data."""
    
    # Get the latest mood rating
    latest_mood = df_mood['mood_rating'].iloc[0] if not df_mood.empty else 0
    
    # Get a list of all habits
    habits = df_habits['name'].tolist() if not df_habits.empty else []

    if latest_mood >= 8:
        return f"You're doing great with a mood of {latest_mood}/10! Keep up the good work and stay positive."
    elif latest_mood >= 4:
        motivational_quotes = [
            "The secret of getting ahead is getting started.",
            "The best way to predict the future is to create it.",
            "Don't watch the clock; do what it does. Keep going.",
            "The future belongs to those who believe in the beauty of their dreams."
        ]
        return f"It looks like your mood is a bit low today at {latest_mood}/10. Here's some motivation: '{random.choice(motivational_quotes)}'"
    else:
        if habits:
            suggested_habit = random.choice(habits)
            return f"Your mood is quite low today. Your Smart Companion suggests focusing on a habit to feel better. How about '{suggested_habit}'?"
        else:
            return "Your mood is quite low today. Please add a habit in the Daily Tracker page to get a suggestion."

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Dashboard", layout="wide")

# --- Custom CSS for a modern, card-based look ---
st.markdown("""
<style>
.metric-card {
    background-color: #262730;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    margin-bottom: 20px;
    border: 1px solid #383a45;
}
.metric-title {
    font-size: 16px;
    font-weight: bold;
    color: #aaaaaa;
}
.metric-value {
    font-size: 32px;
    font-weight: bold;
    color: white;
}
.metric-list {
    font-size: 14px;
    color: white;
    line-height: 1.5;
}
.stContainer {
    border: 1px solid #383a45;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}
</style>
""", unsafe_allow_html=True)


# Use columns to place the title and select box side by side
title_col, select_col = st.columns([4, 1])

with title_col:
    st.title("📊 Your Study Dashboard")

with select_col:
    st.markdown("<br>", unsafe_allow_html=True) # Add some spacing for alignment
    time_frame = st.selectbox(
        "Select Time Frame:",
        ('Last 7 Days', 'Last 30 Days'),
        label_visibility="collapsed" # Hides the label for a cleaner look
    )

if time_frame == 'Last 7 Days':
    time_delta = '-7 days'
else:
    time_delta = '-30 days'

st.write("An organized overview of your well-being, habits, and study progress.")

# --- STUDY TIME ANALYSIS ---
with st.container():
    st.header("Study Effort Breakdown")
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Study Time by Subject")
        conn = get_db_connection()
        df_study = pd.read_sql_query(f"SELECT date, subject, duration_minutes FROM study_sessions WHERE date >= date('now', '{time_delta}') ORDER BY date", conn)
        conn.close()

        if not df_study.empty:
            df_study['duration_hours'] = df_study['duration_minutes'] / 60
            study_by_subject = df_study.groupby('subject')['duration_hours'].sum().reset_index()
            
            # Find the most studied subject
            top_subject_row = study_by_subject.loc[study_by_subject['duration_hours'].idxmax()]
            top_subject_name = top_subject_row['subject']
            top_subject_hours = top_subject_row['duration_hours']

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Most Studied Subject ({time_frame})</div>
                    <div class="metric-value">{top_subject_name} ({top_subject_hours:.1f} hrs)</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            fig_subjects = px.pie(study_by_subject, values='duration_hours', names='subject',
                                  hole=.3,
                                  color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_subjects, use_container_width=True)
        else:
            st.info(f"No study sessions logged yet for the {time_frame.lower()}.")

    with col4:
        st.subheader("Study Time Over Time")
        conn = get_db_connection()
        df_study = pd.read_sql_query(f"SELECT date, subject, duration_minutes FROM study_sessions WHERE date >= date('now', '{time_delta}') ORDER BY date", conn)
        conn.close()
        
        if not df_study.empty:
            df_study['duration_hours'] = df_study['duration_minutes'] / 60
            total_hours = df_study['duration_hours'].sum()
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Total Hours Studied ({time_frame})</div>
                    <div class="metric-value">{total_hours:.1f} hrs</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            df_study['date'] = pd.to_datetime(df_study['date'])
            study_by_date = df_study.groupby('date')['duration_hours'].sum().reset_index()
            fig_time = px.line(study_by_date, x='date', y='duration_hours',
                               labels={'duration_hours': 'Hours Studied', 'date': 'Date'},
                               color_discrete_sequence=['#5DADE2'])
            fig_time.update_layout(
                xaxis_title="", 
                yaxis_title="Hours Studied"
            )
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info(f"Go to the 'Schedule' page to add your study time!")

# --- MOOD & HABIT DASHBOARD ---
with st.container():
    st.header("Daily Trends")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Mood Over Time")
        conn = get_db_connection()
        df_mood_chart = pd.read_sql_query(f"SELECT date, mood_rating FROM mood_logs WHERE date >= date('now', '{time_delta}') ORDER BY date", conn)
        conn.close()


        if not df_mood_chart.empty:
            df_mood_chart['date'] = pd.to_datetime(df_mood_chart['date'])
            average_mood = df_mood_chart['mood_rating'].mean().round(1)
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Average Mood ({time_frame})</div>
                    <div class="metric-value">{average_mood} / 10</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            fig_mood = px.line(df_mood_chart, x='date', y='mood_rating',
                               labels={'mood_rating': 'Mood Rating', 'date': 'Date'},
                               color_discrete_sequence=['#FF6347'])
            fig_mood.update_layout(xaxis_title="", yaxis_title="Mood Rating (1-10)")
            st.plotly_chart(fig_mood, use_container_width=True)
        else:
            st.info(f"No mood data yet for the {time_frame.lower()}. Log your mood to see your feelings!")

    with col2:
        st.subheader("Habit Completion")
        conn = get_db_connection()
        df_habits = pd.read_sql_query("SELECT id, name FROM habits", conn)
        df_completions = pd.read_sql_query(f"SELECT habit_id, COUNT(date) as count FROM habit_completions WHERE date >= date('now', '{time_delta}') GROUP BY habit_id", conn)
        conn.close()

        if not df_habits.empty and not df_completions.empty:
            df_merged = pd.merge(df_habits, df_completions, left_on='id', right_on='habit_id', how='left').fillna(0)
            df_merged['count'] = df_merged['count'].astype(int)
            if not df_merged.empty:
                top_habit = df_merged.loc[df_merged['count'].idxmax()]
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-title">Your Top Habit ({time_frame})</div>
                        <div class="metric-value">{top_habit['name']} ({int(top_habit['count'])}x)</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            fig_habits = px.bar(df_merged, x='name', y='count',
                                labels={'count': 'Times Completed', 'name': 'Habit'},
                                color_discrete_sequence=['#4682B4'])
            fig_habits.update_layout(xaxis_title="", yaxis_title="Times Completed")
            st.plotly_chart(fig_habits, use_container_width=True)
        else:
            st.info(f"No habits or completion data yet for the {time_frame.lower()}. Add some habits and get started!")

# --- AI-Powered Insights ---
st.markdown("---")
st.header("🧠 AI-Powered Insights")
st.markdown("Here, your Smart Companion will analyze your data and give you personalized tips and recommendations.")

# Call the function to generate an insight
conn = get_db_connection()
df_mood_insight = pd.read_sql_query("SELECT date, mood_rating, journal_entry FROM mood_logs ORDER BY date DESC LIMIT 1", conn)
df_habits_insight = pd.read_sql_query("SELECT * FROM habits", conn)
df_completions_insight = pd.read_sql_query("SELECT * FROM habit_completions", conn)
conn.close()

st.info(generate_ai_insight(df_mood_insight, df_habits_insight, df_completions_insight))
