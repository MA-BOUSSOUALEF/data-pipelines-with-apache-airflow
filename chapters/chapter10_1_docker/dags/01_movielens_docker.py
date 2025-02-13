import datetime as dt
import os

from airflow import DAG
from airflow.operators.docker_operator import DockerOperator


with DAG(
    dag_id="01_movielens_docker",
    description="Fetches ratings from the Movielens API using Docker.",
    start_date=dt.datetime(2019, 1, 1),
    end_date=dt.datetime(2019, 1, 3),
    schedule_interval="@daily",
) as dag:

    fetch_ratings = DockerOperator(
        task_id="fetch_ratings",
        image="manning-airflow/ch10-movielens-fetch",
        command=[
            "fetch-ratings",
            "--start_date",
            "{{ds}}",
            "--end_date",
            "{{next_ds}}",
            "--output_path",
            "/data/ratings/{{ds}}.json",
            "--user",
            os.environ["MOVIELENS_USER"],
            "--password",
            os.environ["MOVIELENS_PASSWORD"],
            "--host",
            os.environ["MOVIELENS_HOST"],
        ],
        network_mode="airflow",
        # Note: this host path is on the HOST, not in the Airflow docker container.
        volumes=["/tmp/airflow/data:/data"],
    )

    rank_movies = DockerOperator(
        task_id="rank_movies",
        image="manning-airflow/ch10-movielens-rank",
        command=[
            "rank-movies",
            "--input_path",
            "/data/ratings/{{ds}}.json",
            "--output_path",
            "/data/rankings/{{ds}}.csv",
        ],
        volumes=["/tmp/airflow/data:/data"],
    )

    fetch_ratings >> rank_movies
