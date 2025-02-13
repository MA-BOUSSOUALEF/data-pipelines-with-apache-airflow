import datetime as dt
import os

from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.contrib.kubernetes.volume import Volume
from airflow.contrib.kubernetes.volume_mount import VolumeMount

with DAG(
    dag_id="02_movielens_kubernetes",
    description="Fetches ratings from the Movielens API using kubernetes.",
    start_date=dt.datetime(2019, 1, 1),
    end_date=dt.datetime(2019, 1, 3),
    schedule_interval="@daily",
) as dag:

    volume_mount = VolumeMount(
        "data-volume", mount_path="/data", sub_path=None, read_only=False
    )

    volume_config = {"persistentVolumeClaim": {"claimName": "data-volume"}}
    volume = Volume(name="data-volume", configs=volume_config)

    fetch_ratings = KubernetesPodOperator(
        task_id="fetch_ratings",
        image="manning-airflow/ch10-movielens-fetch",
        cmds=["fetch-ratings"],
        arguments=[
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
        namespace="airflow",
        name="fetch-ratings",
        cluster_context="docker-desktop",
        volumes=[volume],
        volume_mounts=[volume_mount],
    )

    rank_movies = KubernetesPodOperator(
        task_id="rank_movies",
        image="manning-airflow/ch10-movielens-rank",
        cmds=["rank-movies"],
        arguments=[
            "--input_path",
            "/data/ratings/{{ds}}.json",
            "--output_path",
            "/data/rankings/{{ds}}.csv",
        ],
        namespace="airflow",
        name="rank-movies",
        cluster_context="docker-desktop",
        volumes=[volume],
        volume_mounts=[volume_mount],
    )

    fetch_ratings >> rank_movies
