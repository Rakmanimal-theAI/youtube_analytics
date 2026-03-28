# dashboard.py
import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="YouTube Trending Analytics", layout="wide")
st.title("📊 YouTube Trending Videos Analytics Dashboard")

# Snowflake connection (using secrets for security - we'll set this up)
@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data(query):
    conn = init_connection()
    return pd.read_sql(query, conn)

# Sidebar filters
st.sidebar.header("Filters")
category_filter = st.sidebar.multiselect(
    "Select Categories",
    options=["All"]  # We'll populate this dynamically
)

# Main queries
st.subheader("📈 Top Performing Videos")

# Query 1: Top 10 videos by views
top_videos_query = """
SELECT 
    CHANNEL_TITLE,
    COUNT(*) as trending_count,
    AVG(VIEWS) as avg_views,
    AVG(ENGAGEMENT_RATE) as avg_engagement
FROM ANALYTICS.VIDEO_PERFORMANCE
GROUP BY CHANNEL_TITLE
ORDER BY trending_count DESC
LIMIT 10;
"""

top_videos = load_data(top_videos_query)
st.dataframe(top_videos, use_container_width=True)

# Query 2: Category performance
category_query = """
SELECT 
    CATEGORY_NAME,
    COUNT(*) as videos_trended,
    AVG(VIEWS) as avg_views,
    AVG(ENGAGEMENT_RATE) as avg_engagement
FROM ANALYTICS.VIDEO_PERFORMANCE
GROUP BY CATEGORY_NAME
ORDER BY avg_views DESC;
"""

category_data = load_data(category_query)

# Create bar chart
fig = px.bar(
    category_data,
    x="CATEGORY_NAME",
    y="AVG_VIEWS",
    title="Average Views by Category",
    color="AVG_ENGAGEMENT",
    labels={"CATEGORY_NAME": "Category", "avg_views": "Average Views"}
)
st.plotly_chart(fig, use_container_width=True)

# Query 3: Engagement analysis
engagement_query = """
SELECT 
    CASE 
        WHEN VIEWS < 100000 THEN '(<100K)'
        WHEN VIEWS < 1000000 THEN '(100K-1M)'
        ELSE '(>1M)'
    END as view_tier,
    AVG(ENGAGEMENT_RATE) as avg_engagement,
    COUNT(*) as video_count
FROM ANALYTICS.VIDEO_PERFORMANCE
GROUP BY view_tier
ORDER BY avg_engagement DESC;
"""

engagement_data = load_data(engagement_query)

col1, col2 = st.columns(2)

with col1:
    fig2 = px.pie(
        engagement_data,
        values="VIDEO_COUNT",
        names="VIEW_TIER",
        title="Video Distribution by Performance Tier"
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.subheader("Key Metrics")
    total_videos = load_data("SELECT COUNT(*) FROM ANALYTICS.VIDEO_PERFORMANCE").iloc[0,0]
    avg_views = load_data("SELECT AVG(VIEWS) FROM ANALYTICS.VIDEO_PERFORMANCE").iloc[0,0]
    
    st.metric("Total Videos Analyzed", f"{total_videos:,}")
    st.metric("Average Views", f"{avg_views:,.0f}")

# Query 4: Time trend (if you have date data)
st.subheader("📅 Trending Over Time")
time_query = """
SELECT 
    DATE_TRUNC('day', TRENDING_DATE) as trend_day,
    COUNT(*) as videos_trended,
    AVG(VIEWS) as avg_views
FROM ANALYTICS.VIDEO_PERFORMANCE
GROUP BY trend_day
ORDER BY trend_day DESC
LIMIT 30
"""

try:
    time_data = load_data(time_query)
    fig3 = px.line(
        time_data,
        x="TREND_DAY",
        y="VIDEOS_TRENDED",
        title="Number of Trending Videos Over Time"
    )
    st.plotly_chart(fig3, use_container_width=True)
except:
    st.info("Time-based data available after multiple pipeline runs")