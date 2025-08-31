import streamlit as st
import pandas as pd
import sqlite3

# --- DATABASE FUNCTIONS ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('study_companion.db')
    return conn

def update_db(table, row_id, column, new_value):
    """Updates a single value in the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE {table} SET {column} = ? WHERE id = ?", (new_value, row_id))
    conn.commit()
    conn.close()

def delete_from_db(table, row_id):
    """Deletes a single row from the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Records", layout="wide")
st.title("📝 Your Records")
st.write("A complete overview of all your logged data.")

st.markdown("---")

# --- SEARCH BAR ---
search_query = st.text_input("🔍 Search records by keyword:")

def filter_dataframe(df, query):
    if not query:
        return df
    
    query = query.lower()
    df_filtered = df.copy()
    
    # Check all string columns for the query
    string_cols = df_filtered.select_dtypes(include=['object']).columns
    df_filtered = df_filtered[df_filtered[string_cols].apply(
        lambda x: x.str.lower().str.contains(query, na=False)
    ).any(axis=1)]
    return df_filtered

# --- MOOD LOGS TABLE ---
st.header("😊 Mood Logs")
conn = get_db_connection()
df_moods = pd.read_sql_query("SELECT id, date, mood_rating, journal_entry FROM mood_logs ORDER BY date DESC", conn, index_col='id')
conn.close()

if not df_moods.empty:
    df_moods['date'] = pd.to_datetime(df_moods['date']) # Convert to datetime for editing
    df_moods.index = range(1, len(df_moods) + 1)
    df_moods_filtered = filter_dataframe(df_moods, search_query)
    edited_df = st.data_editor(df_moods_filtered, use_container_width=True, num_rows='dynamic', 
                               column_config={
                                   "date": st.column_config.DateColumn("Date"),
                                   "mood_rating": st.column_config.NumberColumn("Mood (1-10)"),
                                   "journal_entry": st.column_config.TextColumn("Journal Entry")
                               })

    # Find deleted rows
    if edited_df is not None:
        deleted_rows = list(set(df_moods_filtered.index) - set(edited_df.index))
        if deleted_rows:
            for row_id in deleted_rows:
                delete_from_db('mood_logs', row_id)
            st.success(f"Deleted {len(deleted_rows)} record(s) from Mood Logs.")
            st.rerun()

    # Find updated rows
    if edited_df is not None and not edited_df.equals(df_moods_filtered):
        for row_id, row in edited_df.iterrows():
            original_row = df_moods_filtered.loc[row_id]
            for col in row.index:
                if row[col] != original_row[col]:
                    update_db('mood_logs', row_id, col, row[col])
        st.success("Mood Logs updated successfully!")
        st.rerun()
else:
    st.info("No mood logs found.")

st.markdown("---")

# --- HABIT COMPLETIONS TABLE ---
st.header("✅ Habit Completions")
conn = get_db_connection()
df_habits = pd.read_sql_query("""
    SELECT hc.id, h.name AS habit, hc.date AS date
    FROM habit_completions hc
    JOIN habits h ON hc.habit_id = h.id
    ORDER BY hc.date DESC
""", conn, index_col='id')
conn.close()

if not df_habits.empty:
    df_habits['date'] = pd.to_datetime(df_habits['date']) # Convert to datetime for editing
    df_habits.index = range(1, len(df_habits) + 1)
    df_habits_filtered = filter_dataframe(df_habits, search_query)
    edited_df_habits = st.data_editor(df_habits_filtered, use_container_width=True, num_rows='dynamic', 
                                      column_config={
                                          "date": st.column_config.DateColumn("Date"),
                                          "habit": st.column_config.TextColumn("Habit")
                                      })

    # Find deleted rows
    if edited_df_habits is not None:
        deleted_rows = list(set(df_habits_filtered.index) - set(edited_df_habits.index))
        if deleted_rows:
            for row_id in deleted_rows:
                delete_from_db('habit_completions', row_id)
            st.success(f"Deleted {len(deleted_rows)} record(s) from Habit Completions.")
            st.rerun()
            
    # Find updated rows
    if edited_df_habits is not None and not edited_df_habits.equals(df_habits_filtered):
        for row_id, row in edited_df_habits.iterrows():
            original_row = df_habits_filtered.loc[row_id]
            for col in row.index:
                if row[col] != original_row[col]:
                    update_db('habit_completions', row_id, col, row[col])
        st.success("Habit Completions updated successfully!")
        st.rerun()

else:
    st.info("No habit completions found.")

st.markdown("---")

# --- STUDY SESSIONS TABLE ---
st.header("🗓️ Study Sessions")
conn = get_db_connection()
df_study = pd.read_sql_query("SELECT id, date, subject, duration_minutes, notes FROM study_sessions ORDER BY date DESC", conn, index_col='id')
conn.close()

if not df_study.empty:
    df_study['date'] = pd.to_datetime(df_study['date']) # Convert to datetime for editing
    df_study['duration_hours'] = (df_study['duration_minutes'] / 60).round(2)
    df_study = df_study.drop(columns=['duration_minutes'])
    df_study.rename(columns={'duration_hours': 'Hours Studied'}, inplace=True)
    df_study.index = range(1, len(df_study) + 1)
    
    df_study_filtered = filter_dataframe(df_study, search_query)
    edited_df_study = st.data_editor(df_study_filtered, use_container_width=True, num_rows='dynamic',
                                     column_config={
                                         "date": st.column_config.DateColumn("Date"),
                                         "subject": st.column_config.TextColumn("Subject"),
                                         "Hours Studied": st.column_config.NumberColumn("Hours Studied"),
                                         "notes": st.column_config.TextColumn("Notes")
                                     })

    # Find deleted rows
    if edited_df_study is not None:
        deleted_rows = list(set(df_study_filtered.index) - set(edited_df_study.index))
        if deleted_rows:
            for row_id in deleted_rows:
                delete_from_db('study_sessions', row_id)
            st.success(f"Deleted {len(deleted_rows)} record(s) from Study Sessions.")
            st.rerun()

    # Find updated rows
    if edited_df_study is not None and not edited_df_study.equals(df_study_filtered):
        for row_id, row in edited_df_study.iterrows():
            original_row = df_study_filtered.loc[row_id]
            for col in row.index:
                if col == "Hours Studied":
                    # Special handling for duration_minutes
                    update_db('study_sessions', row_id, 'duration_minutes', int(row[col] * 60))
                elif row[col] != original_row[col]:
                    update_db('study_sessions', row_id, col, row[col])
        st.success("Study Sessions updated successfully!")
        st.rerun()
else:
    st.info("No study sessions found.")
