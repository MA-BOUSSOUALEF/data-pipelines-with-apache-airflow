import datetime as dt
from pathlib import Path

import pandas as pd

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

dag = DAG(
    dag_id="03_11_non_atomic_send",
    schedule_interval="@daily",
    start_date=dt.datetime(year=2019, month=1, day=1),
    end_date=dt.datetime(year=2019, month=1, day=5),
    catchup=True,
)

fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command=(
        "mkdir -p /opt/airflow/data/events && "
        "curl -o /opt/airflow/data/events/{{ds}}.json "
        "http://events_api:5000/events?"
        "start_date={{ds}}&"
        "end_date={{next_ds}}"
    ),
    dag=dag,
)


def _calculate_stats(**context):
    """Calculates event statistics."""
    input_path = context["templates_dict"]["input_path"]
    output_path = context["templates_dict"]["output_path"]

    events = pd.read_json(input_path)
    stats = events.groupby(["date", "user"]).size().reset_index()

    Path(output_path).parent.mkdir(exist_ok=True)
    stats.to_csv(output_path, index=False)

    _email_stats(stats, email="user@example.com")                   # @NOTE Sending an email after writing to CSV 
                                                                    # creates two pieces of work in a single function, 
                                                                    # which breaks the atomicity of the task.


def _email_stats(stats, email):
    """Send an email..."""
    print(f"Sending stats to {email}...")


calculate_stats = PythonOperator(
    task_id="calculate_stats",
    python_callable=_calculate_stats,
    templates_dict={
        "input_path": "/opt/airflow/data/events/{{ds}}.json",
        "output_path": "/opt/airflow/data/stats/{{ds}}.csv",
    },
    provide_context=True,
    dag=dag,
)

fetch_events >> calculate_stats