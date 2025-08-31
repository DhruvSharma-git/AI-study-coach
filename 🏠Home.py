import streamlit as st

st.set_page_config(page_title="Smart Study Companion", layout="wide")

st.title("The Smart Study Companion")
st.write("Your personal assistant for smarter studying.")

st.markdown("""
<style>
/* Card styling */
.nav-card {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    background-color: #1f2730;
    border: 2px solid #333333;
    border-radius: 15px;
    padding: 30px 10px;
    margin-bottom: 20px;
    cursor: pointer;
    transition: transform 0.2s ease-in-out;
    text-decoration: none !important;
    color: white !important;
}
.nav-card:hover {
    transform: scale(1.05);
    background-color: #262f3a;
}

/* Remove blue underline from links */
.nav-card:link, .nav-card:visited, .nav-card:hover, .nav-card:active {
    text-decoration: none !important;
    color: white !important;
}

/* Inner styles */
.nav-icon {
    font-size: 3rem;
    line-height: 1;
}
.nav-label {
    font-size: 20px;
    font-weight: bold;
    margin-top: 10px;
}
.nav-description {
    font-size: 14px;
    color: #aaaaaa;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("---")
st.header("What this app can do for you:")

# Row 1
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <a href="/Schedule" target="_self" class="nav-card">
            <div class="nav-icon">🗓️</div>
            <div class="nav-label">Schedule</div>
            <div class="nav-description">Plan your weekly study hours and subjects.</div>
        </a>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <a href="/Daily_Trackers" target="_self" class="nav-card">
            <div class="nav-icon">😊✅</div>
            <div class="nav-label">Daily Trackers</div>
            <div class="nav-description">Log your mood and track your daily habits.</div>
        </a>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# Row 2
col3, col4 = st.columns(2)

with col3:
    st.markdown(
        """
        <a href="/Dashboard" target="_self" class="nav-card">
            <div class="nav-icon">📊</div>
            <div class="nav-label">Dashboard</div>
            <div class="nav-description">Visualize your trends and gain insights.</div>
        </a>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        """
        <a href="/Records" target="_self" class="nav-card">
            <div class="nav-icon">📝</div>
            <div class="nav-label">Records</div>
            <div class="nav-description">View your historical data and logs.</div>
        </a>
        """,
        unsafe_allow_html=True
    )
