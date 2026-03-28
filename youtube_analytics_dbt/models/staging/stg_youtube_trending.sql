-- staging/stg_youtube_trending.sql
SELECT
    video_id,
    title,
    channel_title,
    category_id,
    published_at::TIMESTAMP as published_at,
    view_count::INTEGER as views,
    like_count::INTEGER as likes,
    comment_count::INTEGER as comments,
    duration,
    trending_date,
    fetched_at,
    (like_count + comment_count) * 100.0 / NULLIF(view_count, 0) as engagement_rate,
    DATEDIFF('day', published_at::DATE, trending_date) as days_to_trend
FROM {{ source('raw', 'youtube_trending') }}
WHERE view_count > 0
