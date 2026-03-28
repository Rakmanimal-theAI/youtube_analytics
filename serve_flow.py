from prefect_flow import youtube_pipeline

if __name__ == "__main__":
    # Serve the flow with a daily schedule at 9 AM UTC
    youtube_pipeline.serve(
        name="daily-youtube-pipeline",
        cron="0 9 * * *",
        parameters={}
    )