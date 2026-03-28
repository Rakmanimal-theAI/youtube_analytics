-- marts/video_performance.sql
WITH category_mapping AS (
    SELECT * FROM (VALUES
        (1, 'Film & Animation'), (2, 'Autos & Vehicles'), (10, 'Music'),
        (15, 'Pets & Animals'), (17, 'Sports'), (19, 'Travel & Events'),
        (20, 'Gaming'), (22, 'People & Blogs'), (23, 'Comedy'),
        (24, 'Entertainment'), (25, 'News & Politics'), (26, 'Howto & Style'),
        (27, 'Education'), (28, 'Science & Technology'), (29, 'Nonprofits & Activism')
    ) AS t(category_id, category_name)
)

SELECT
    s.video_id,
    s.title,
    s.channel_title,
    COALESCE(c.category_name, 'Other') as category_name,
    s.published_at,
    s.trending_date,
    s.views,
    s.likes,
    s.comments,
    s.engagement_rate,
    s.days_to_trend,
    CASE 
        WHEN s.views < 100000 THEN 'Bronze (<100K)'
        WHEN s.views < 1000000 THEN 'Silver (100K-1M)'
        ELSE 'Gold (>1M)'
    END as performance_tier,
    CURRENT_TIMESTAMP() as updated_at
FROM {{ ref('stg_youtube_trending') }} s
LEFT JOIN category_mapping c ON s.category_id = c.category_id
