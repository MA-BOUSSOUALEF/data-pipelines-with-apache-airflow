from datetime import datetime
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

dag = DAG(
    dag_id="03_02_daily_schedule",
    start_date=datetime(2019, 1, 1),    # @NOTE Date/time to start scheduling DAG runs
    end_date=datetime(2019, 1, 5),
    schedule_interval="@daily",         # @NOTE Schedule the DAG to run every day at midnight.
)

fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command=(
        "mkdir -p /opt/airflow/data/events && "
        "curl -o /opt/airflow/data/events.json http://events_api:5000/events"
    ),
    dag=dag,
)


def _calculate_stats(input_path, output_path):
    """Calculates event statistics."""

    print(f"will read input_path={input_path}")
    events = pd.read_json(input_path)
    stats = events.groupby(["date", "user"]).size().reset_index()
    print("finished grouping")
    Path(output_path).parent.mkdir(exist_ok=True)
    print("finished creating dir")
    stats.to_csv(output_path, index=False)
    print("finished function")


calculate_stats = PythonOperator(
    task_id="calculate_stats",
    python_callable=_calculate_stats,
    op_kwargs={"input_path": "/opt/airflow/data/events.json", "output_path": "/opt/airflow/data/stats.csv"},
    dag=dag,
)

fetch_events >> calculate_stats
