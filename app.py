import streamlit as st
import pandas as pd
import plotly.express as px

# Configure the page settings
st.set_page_config(page_title="Khan Academy YouTube Dashboard", layout="wide", page_icon=":bar_chart:")

# --- Custom CSS Styling for Visual Appeal ---
st.markdown(
    """
    <style>
    /* Overall background styling */
    .reportview-container {
        background: #f5f5f5;
    }
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #ffffff;
    }
    /* Title styling */
    h1 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #2F4F4F;
        text-align: center;
    }
    h3 {
        text-align: center;
        color: #2F4F4F;
    }
    /* Footer styling */
    .footer {
        text-align: center;
        font-size: 12px;
        color: #888888;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Data Loading Function using the new caching decorator ---
@st.cache_data
def load_data():
    # Load data from the CSV file (ensure the file is in the same directory)
    df = pd.read_csv("khan_academy_videos.csv")
    # Convert 'publishedAt' to timezone-aware datetime objects (UTC)
    df['publishedAt'] = pd.to_datetime(df['publishedAt'], utc=True)
    
    # Create the engagementRate feature if it doesn't already exist
    if 'engagementRate' not in df.columns:
        df['engagementRate'] = (
            pd.to_numeric(df['likeCount'], errors='coerce') +
            pd.to_numeric(df['commentCount'], errors='coerce')
        ) / pd.to_numeric(df['viewCount'], errors='coerce')
    return df

df = load_data()

# --- Dashboard Header ---
st.title("Khan Academy YouTube Engagement Dashboard")
st.markdown("<h3>Created by Vartika Singh</h3>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("### Use the filters in the sidebar to explore engagement metrics of Khan Academy's YouTube videos.")

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")
start_date = st.sidebar.date_input("Start Date", df['publishedAt'].min().date())
end_date = st.sidebar.date_input("End Date", df['publishedAt'].max().date())

if start_date > end_date:
    st.sidebar.error("Error: Start date must be before end date.")

# Convert input dates to timezone-aware datetime objects in UTC
start_date = pd.to_datetime(start_date).tz_localize('UTC')
end_date = pd.to_datetime(end_date).tz_localize('UTC')

# Filter the DataFrame based on the selected date range
filtered_df = df[(df['publishedAt'] >= start_date) & (df['publishedAt'] <= end_date)]

# Engagement metric selection
metric = st.sidebar.selectbox(
    "Select Engagement Metric",
    ("viewCount", "likeCount", "commentCount", "engagementRate")
)

# --- Main Dashboard Content ---
st.markdown(f"### Videos from {start_date.date()} to {end_date.date()}")
st.markdown(f"#### Displaying **{metric}** for each video")

if not filtered_df.empty:
    # Sort the filtered DataFrame by the selected metric
    filtered_df_sorted = filtered_df.sort_values(by=metric, ascending=False)
    
    # Create an interactive bar chart using Plotly Express
    fig = px.bar(
        filtered_df_sorted,
        x='title',
        y=metric,
        hover_data=['publishedAt'],
        title=f"{metric} per Video",
        labels={'title': 'Video Title', metric: metric}
    )
    # Increase chart height for better vertical viewability and update layout
    fig.update_layout(
        height=800,             # Increased vertical height (800 pixels)
        xaxis_tickangle=-45,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.markdown("### No videos available for the selected date range.")

# Optionally display raw data
if st.sidebar.checkbox("Show Raw Data"):
    st.subheader("Raw Data")
    st.write(filtered_df)

# --- Footer Attribution ---
st.markdown("<div class='footer'>Created by Vartika Singh</div>", unsafe_allow_html=True)
