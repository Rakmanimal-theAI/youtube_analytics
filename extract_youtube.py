# extract_youtube.py
import os
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration - now loaded from .env
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "YT_WH")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "YT_TRENDING_DB")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "RAW")

def fetch_trending_videos(region_code="US", max_results=50):
    """Fetch trending videos from YouTube API using API key"""
    
    # Build the service with API key (NOT OAuth credentials)
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    # API call
    request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        chart="mostPopular",
        regionCode=region_code,
        maxResults=max_results
    )
    response = request.execute()
    
    videos = []
    for item in response.get("items", []):
        video_data = {
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "channel_title": item["snippet"]["channelTitle"],
            "category_id": item["snippet"]["categoryId"],
            "published_at": item["snippet"]["publishedAt"],
            "view_count": int(item["statistics"].get("viewCount", 0)),
            "like_count": int(item["statistics"].get("likeCount", 0)),
            "comment_count": int(item["statistics"].get("commentCount", 0)),
            "duration": item["contentDetails"]["duration"],
            "trending_date": datetime.utcnow().date().isoformat(),
            "fetched_at": datetime.utcnow().isoformat()
        }
        videos.append(video_data)
    
    return pd.DataFrame(videos)

def load_to_snowflake(df):
    """Load data to Snowflake raw table (incremental)"""
    conn = snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,  # This sets the database at connection time
        schema=SNOWFLAKE_SCHEMA        # This sets the schema at connection time
    )
    
    # Create table using fully qualified name (database.schema.table)
    conn.cursor().execute(f"""
        CREATE TABLE IF NOT EXISTS {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.YOUTUBE_TRENDING (
            video_id VARCHAR PRIMARY KEY,
            title VARCHAR,
            channel_title VARCHAR,
            category_id VARCHAR,
            published_at TIMESTAMP,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            duration VARCHAR,
            trending_date DATE,
            fetched_at TIMESTAMP
        )
    """)
    
    # Incremental load using MERGE with fully qualified name
    inserted_count = 0
    updated_count = 0
    
    for _, row in df.iterrows():
        cursor = conn.cursor()
        cursor.execute(f"""
            MERGE INTO {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.YOUTUBE_TRENDING t
            USING (SELECT %s AS video_id) s
            ON t.video_id = s.video_id
            WHEN MATCHED THEN UPDATE SET
                view_count = %s,
                like_count = %s,
                comment_count = %s,
                trending_date = %s,
                fetched_at = %s
            WHEN NOT MATCHED THEN INSERT
                (video_id, title, channel_title, category_id, 
                 published_at, view_count, like_count, comment_count, 
                 duration, trending_date, fetched_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row["video_id"], 
            row["view_count"], row["like_count"], row["comment_count"], 
            row["trending_date"], row["fetched_at"],
            row["video_id"], row["title"], row["channel_title"],
            row["category_id"], row["published_at"], row["view_count"],
            row["like_count"], row["comment_count"], row["duration"],
            row["trending_date"], row["fetched_at"]
        ))
        cursor.close()
    
    conn.close()
    print(f"✅ Loaded {len(df)} videos to Snowflake")
    return len(df)

if __name__ == "__main__":
    print("📡 Fetching trending videos from YouTube...")
    
    # Verify API key is loaded
    if not YOUTUBE_API_KEY:
        print("❌ ERROR: YOUTUBE_API_KEY not found in .env file")
        print("Please add: YOUTUBE_API_KEY=your_key_here")
        exit(1)
    
    print(f"✅ API key loaded (first 10 chars: {YOUTUBE_API_KEY[:10]}...)")
    
    df = fetch_trending_videos(max_results=50)
    print(f"📊 Fetched {len(df)} videos")
    
    if len(df) > 0:
        print("Sample video:", df.iloc[0]["title"])
        count = load_to_snowflake(df)
        print(f"🎉 Pipeline complete! {count} records processed")
    else:
        print("⚠️ No videos fetched. Check your API key and region.")