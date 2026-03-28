-- tests/generic/test_engagement_not_spike.sql
-- Fails if any video has engagement rate > 5x the average
SELECT *
FROM {{ ref('stg_youtube_trending') }}
WHERE engagement_rate > (
    SELECT AVG(engagement_rate) * 5
    FROM {{ ref('stg_youtube_trending') }}
)
