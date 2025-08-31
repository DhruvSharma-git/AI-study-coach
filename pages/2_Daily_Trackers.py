import streamlit as st
import pandas as pd
import datetime
import sqlite3
import plotly.express as px

# --- DATABASE FUNCTIONS ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('study_companion.db')
    return conn

def create_tables():
    """Creates the necessary tables in the database if they do not exist."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            mood_rating INTEGER,
            mood_label TEXT,
            mood_emoji TEXT,
            journal_entry TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS habit_completions (
            id INTEGER PRIMARY KEY,
            habit_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_mood(mood_rating, mood_label, mood_emoji, journal_entry):
    """Logs the user's mood to the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO mood_logs (date, mood_rating, mood_label, mood_emoji, journal_entry) VALUES (?, ?, ?, ?, ?)",
        (datetime.date.today().isoformat(), mood_rating, mood_label, mood_emoji, journal_entry)
    )
    conn.commit()
    conn.close()

# --- UI FOR DAILY TRACKERS PAGE ---
st.set_page_config(page_title="Daily Trackers", layout="wide")
st.title("😊✅ Daily Tracking")
st.write("Log your mood and track your habits to see how they influence your study schedule.")

# Ensure tables are created when the app starts
create_tables()

# Create tabs for the layout
tab_mood, tab_habits = st.tabs(["😊 Mood Log", "✅ Habit Tracker"])

# ---- MOOD LOG TAB ----
with tab_mood:
    st.header("Mood Log")

    # Mood Slider (Moved outside the form to enable real-time updates)
    mood_value = st.slider("How are you feeling today?", 1, 10, 5)

    # Map slider value → Emoji + Label
    if mood_value <= 2:
        mood_emoji, mood_label = "😢", "Very Sad"
    elif mood_value <= 4:
        mood_emoji, mood_label = "😞", "Sad"
    elif mood_value <= 6:
        mood_emoji, mood_label = "😐", "Neutral"
    elif mood_value <= 8:
        mood_emoji, mood_label = "🙂", "Happy"
    elif mood_value == 9:
        mood_emoji, mood_label = "😄", "Very Happy"
    else:  # mood_value == 10
        mood_emoji, mood_label = "🤩", "Excited"

    st.markdown(f"### Your mood: {mood_emoji} {mood_label} ({mood_value}/10)")

    with st.form(key='mood_form'):
        journal_entry = st.text_area("📝 Want to add a short journal entry?", "")

        if st.form_submit_button("Save Today's Mood"):
            log_mood(mood_value, mood_label, mood_emoji, journal_entry)
            st.success("✅ Mood logged successfully!")

    st.markdown("---")

    # Mood Trends Chart
    st.subheader("Mood Trends (Past 7 Days)")
    conn = get_db_connection()
    df_mood = pd.read_sql_query("SELECT date, mood_rating FROM mood_logs ORDER BY date DESC LIMIT 7", conn)
    conn.close()
    
    if not df_mood.empty:
        df_mood = df_mood.sort_values("date")
        fig = px.line(df_mood, x='date', y='mood_rating', title='Your Mood Over Time', markers=True)
        st.plotly_chart(fig)
    else:
        st.info("No mood data yet. Log your mood to see trends!")

# ---- HABIT TRACKER TAB ----
with tab_habits:
    st.header("Habit Tracker")
    with st.form(key='habit_tracker_form'):
        new_habit_name = st.text_input("Add a new habit:")
        add_habit_button = st.form_submit_button(label='Add Habit')
        if add_habit_button and new_habit_name:
            conn = get_db_connection()
            c = conn.cursor()
            try:
                c.execute("INSERT INTO habits (name) VALUES (?)", (new_habit_name,))
                conn.commit()
                st.success(f"Habit '{new_habit_name}' added!")
            except sqlite3.IntegrityError:
                st.warning("Habit already exists.")
            conn.close()

    st.markdown("---")
    st.subheader("Today's Habits")
    conn = get_db_connection()
    df_habits = pd.read_sql_query("SELECT id, name FROM habits", conn)
    df_completions = pd.read_sql_query("SELECT habit_id, date FROM habit_completions WHERE date = ?", conn, params=(datetime.date.today().strftime('%Y-%m-%d'),))
    conn.close()

    if not df_habits.empty:
        for index, row in df_habits.iterrows():
            habit_id = row['id']
            habit_name = row['name']
            
            completed_today = habit_id in df_completions['habit_id'].values
            
            if completed_today:
                st.success(f"✔️ {habit_name} - Completed Today!")
            else:
                if st.button(f"Mark as Complete: {habit_name}", key=f"complete_{habit_id}"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO habit_completions (habit_id, date) VALUES (?, ?)", (habit_id, datetime.date.today().strftime('%Y-%m-%d')))
                        conn.commit()
                        st.success(f"Habit '{habit_name}' marked as complete!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.info(f"You already completed '{habit_name}' today.")
                    conn.close()
    else:
        st.info("No habits added yet. Add some above!")