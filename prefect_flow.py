from prefect import flow, task
import subprocess

@task
def extract_youtube():
    result = subprocess.run(["python3", "extract_youtube.py"], capture_output=True, text=True)
    print(result.stdout)
    return "Extraction complete"

@task  
def run_dbt():
    result = subprocess.run(["dbt", "run", "--project-dir", "youtube_analytics_dbt"], capture_output=True, text=True)
    print(result.stdout)
    return "dbt complete"

@flow(name="youtube-daily-pipeline")
def youtube_pipeline():
    extract_youtube()
    run_dbt()

if __name__ == "__main__":
    youtube_pipeline()