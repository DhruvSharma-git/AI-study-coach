import streamlit as st
import pandas as pd
import random
import datetime
import plotly.express as px
import sqlite3

# --- DATABASE FUNCTIONS ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('study_companion.db')
    return conn

def create_tables():
    """Creates the necessary tables in the database if they do not exist."""
    conn = sqlite3.connect('study_companion.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            mood_rating INTEGER,
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

# --- CALLBACK FUNCTION TO SAVE SCHEDULE ---
def save_schedule_to_db():
    """Saves the generated schedule from session state to the database."""
    if st.session_state.generated_schedule:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Clear previous saved schedule to avoid duplicates
        c.execute("DELETE FROM study_sessions")
        conn.commit()

        # Get today's date and find the starting day of the week
        today_date = datetime.date.today()
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Determine the date of the first day of the schedule (e.g., this Monday)
        start_of_week = today_date - datetime.timedelta(days=today_date.weekday())
        
        # Iterate through the generated schedule and save to database
        for i, day_name in enumerate(days_of_week):
            current_date = start_of_week + datetime.timedelta(days=i)
            sessions = st.session_state.generated_schedule.get(day_name, [])
            for subj, hrs in sessions:
                if subj not in ["Other Activities", "Free Time"]: # Don't save non-study tasks
                    c.execute("INSERT INTO study_sessions (date, subject, duration_minutes, notes) VALUES (?, ?, ?, ?)",
                              (current_date.strftime('%Y-%m-%d'), subj, int(hrs * 60), "")) # Convert hours to minutes
        
        conn.commit()
        conn.close()
        st.success("Schedule saved successfully! Your dashboard will be updated.")
        st.session_state.schedule_saved = True # Set a flag to show success message


# --- SCHEDULE GENERATOR LOGIC ---
def generate_weekly_schedule(subject_difficulty: dict, hours_per_day: int):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    schedule = {day: [] for day in days}

    if not subject_difficulty:
        return schedule

    total_difficulty = sum(subject_difficulty.values())
    weekly_target = hours_per_day * 7

    weekly_allocations = {
        subj: round(weekly_target * (diff / total_difficulty), 1)
        for subj, diff in subject_difficulty.items()
    }

    remaining_alloc = weekly_allocations.copy()
    hardest = max(subject_difficulty, key=subject_difficulty.get)

    for day in days:
        todays_subjects = []
        remaining = hours_per_day

        subjects_today = list(subject_difficulty.keys())
        random.shuffle(subjects_today)

        for subj in subjects_today:
            if remaining <= 0 or remaining_alloc[subj] <= 0:
                continue

            remaining_days = 7 - days.index(day)
            ideal_share = remaining_alloc[subj] / remaining_days if remaining_days > 0 else remaining_alloc[subj]

            slice_time = round(random.uniform(0.8, 1.2) * ideal_share, 1)
            slice_time = min(slice_time, remaining_alloc[subj], remaining)

            if slice_time > 0:
                todays_subjects.append((subj, slice_time))
                remaining_alloc[subj] -= slice_time
                remaining -= slice_time

        max_free = round(hours_per_day * 0.2, 1)
        if remaining > 0.3:
            free_time = min(remaining, max_free)
            if free_time >= 0.1:
                todays_subjects.append(("Other Activities", round(free_time, 1)))
                remaining -= free_time

        if remaining > 0:
            todays_subjects.append((hardest, round(remaining, 1)))
            remaining_alloc[hardest] -= remaining
            remaining = 0

        total_today = round(sum(t[1] for t in todays_subjects), 1)
        diff = round(hours_per_day - total_today, 1)
        if abs(diff) >= 0.1:
            applied = False
            for idx, (s, h) in enumerate(todays_subjects):
                if s == hardest:
                    todays_subjects[idx] = (s, round(h + diff, 1))
                    remaining_alloc[hardest] -= diff
                    applied = True
                    break
            if not applied:
                todays_subjects.append((hardest, round(diff, 1)))
                remaining_alloc[hardest] -= diff

        schedule[day] = todays_subjects

    return schedule

# --- UI FOR SCHEDULE PAGE ---
st.set_page_config(page_title="Schedule", layout="wide")
create_tables()

# --- INITIALIZE SESSION STATE ---
if 'generated_schedule' not in st.session_state:
    st.session_state.generated_schedule = None
if 'schedule_button_clicked' not in st.session_state:
    st.session_state.schedule_button_clicked = False
if 'subject_data' not in st.session_state:
    st.session_state.subject_data = {}
if 'subj_name_input_value' not in st.session_state:
    st.session_state.subj_name_input_value = ""
if 'hours_per_day' not in st.session_state:
    st.session_state.hours_per_day = 6
if 'mood_is_bad' not in st.session_state:
    st.session_state.mood_is_bad = False
if 'schedule_saved' not in st.session_state:
    st.session_state.schedule_saved = False


# Use columns for a clean layout and place the save button on the right
title_col, button_col = st.columns([4, 1])

with title_col:
    st.title("🗓️ Smart Study Schedule Generator")

# Logic for the save button
with button_col:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.generated_schedule is not None:
        st.button("Save Schedule", on_click=save_schedule_to_db)

st.write("Generate a weekly study plan based on your available hours and subject difficulties.")
st.markdown("---")

# ---- Sidebar content for Schedule page ----
with st.sidebar:
    st.header("⚙️ Setup Your Schedule")
    st.session_state.hours_per_day = st.number_input("Available Study Hours per Day", min_value=1, max_value=24, value=st.session_state.hours_per_day)

    st.subheader("📚 Add Subjects")
    with st.form(key='add_subject_form'):
        subj_name = st.text_input("Subject Name", value=st.session_state.subj_name_input_value)
        diff_value = st.slider(f"Difficulty of {subj_name or 'the subject'}", 1, 5, 3)
        add_btn = st.form_submit_button("Add Subject")

    if add_btn and subj_name:
        st.session_state.subject_data[subj_name] = diff_value
        st.session_state.schedule_button_clicked = False
        st.session_state.subj_name_input_value = ""
        st.session_state.schedule_saved = False # Reset save flag
        st.success(f"Subject '{subj_name}' added with difficulty {diff_value}")
        st.rerun()
    
    st.subheader("Current Subjects")
    if st.session_state.subject_data:
        current_subjects = list(st.session_state.subject_data.keys())
        for subj in current_subjects:
            st.write(f"- **{subj}** (Difficulty: {st.session_state.subject_data[subj]})")
    else:
        st.info("No subjects added yet.")
    
    st.write("---")
    if st.button("Generate New Schedule", disabled=not st.session_state.subject_data):
        st.session_state.schedule_button_clicked = True
        st.session_state.schedule_saved = False # Reset save flag
        st.rerun()


# --- Main content for Schedule page ----

# Check for the latest mood
conn = get_db_connection()
latest_mood = pd.read_sql_query("SELECT mood_rating FROM mood_logs ORDER BY date DESC LIMIT 1", conn)
conn.close()

if not latest_mood.empty and latest_mood['mood_rating'].iloc[0] < 4 and not st.session_state.schedule_button_clicked:
    st.session_state.mood_is_bad = True
else:
    st.session_state.mood_is_bad = False

if st.session_state.mood_is_bad:
    st.markdown("---")
    st.header("Hold on! Your mood seems low today.")
    st.warning("Take a break and focus on a habit to feel better before studying.")
    
    st.subheader("Suggested Habit: Take a 20-minute Walk 🚶")
    st.info("Mark this habit as complete in the 'Daily Trackers' tab and come back.")
    
elif not st.session_state.schedule_button_clicked:
    st.markdown("---")
    st.header("Ready to plan your week?")
    st.write("Click the button below to generate your first schedule.")
    if st.button("Generate Schedule", disabled=not st.session_state.subject_data):
        st.session_state.schedule_button_clicked = True
        st.rerun()
else:
    schedule = generate_weekly_schedule(st.session_state.subject_data, st.session_state.hours_per_day)
    st.session_state.generated_schedule = schedule
    
    if not latest_mood.empty:
        if latest_mood['mood_rating'].iloc[0] > 7:
            st.success("Your mood is great! Let's get this done. 🎉")
        elif latest_mood['mood_rating'].iloc[0] >= 4:
            st.info("Remember, a little progress each day adds up to big results. Let's plan it out!")
    
    today_idx = datetime.datetime.today().weekday()
    days_ordered = list(schedule.keys())[today_idx:] + list(schedule.keys())[:today_idx]
    today_name = days_ordered[0]

    st.subheader("📊 Weekly Study Plan")
    df_rows = []
    for day in schedule:
        row = {"Day": day}
        for subj, hrs in schedule[day]:
            row[subj] = row.get(subj, 0) + hrs
        df_rows.append(row)
    df = pd.DataFrame(df_rows).fillna(0)
    df = df.set_index("Day").reindex(days_ordered).reset_index()
    st.dataframe(df, use_container_width=True)

    st.subheader(f"🗓️ Focus for Today: {today_name}")
    today_tasks = schedule[today_name]
    if today_tasks:
        for subj, hrs in today_tasks:
            st.markdown(f"- **{subj}** → {hrs} hrs")
    else:
        st.info("No subjects scheduled today. Full free time 🎉")

    st.subheader("📈 Weekly Time Distribution")
    subject_totals = {}
    for day in schedule:
        for subj, hrs in schedule[day]:
            subject_totals[subj] = subject_totals.get(subj, 0) + hrs
    chart_data = pd.DataFrame(subject_totals.items(), columns=["Subject", "Hours"])
    fig = px.bar(
        chart_data,
        x="Subject",
        y="Hours",
        title="Total Hours per Subject (Weekly)",
        height=500,
        color_discrete_sequence=['#1f77b4']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_font_color="white",
        font_color="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#555555')
    )
    st.plotly_chart(fig, use_container_width=True)
