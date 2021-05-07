import datetime as dt
from datetime import timedelta
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

dag = DAG(
    dag_id="03_09_templated_path",
    schedule_interval=timedelta(days=3),
    start_date=dt.datetime(year=2019, month=1, day=1),
    end_date=dt.datetime(year=2019, month=1, day=5),
)

fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command=(
        "mkdir -p /opt/airflow/data/events && "
        "curl -o /opt/airflow/data/events/{{ds}}.json "   # @NOTE we will have:
                                              # /opt/airflow/data/events/2019-01-01.json
                                              # /opt/airflow/data/events/2019-01-02.json
                                              # /opt/airflow/data/events/2019-01-03.json
                                              # /opt/airflow/data/events/2019-01-04.json
                                              # ...
        "http://events_api:5000/events?"
        "start_date={{ds}}&"
        "end_date={{next_ds}}"
    ),
    dag=dag,
)


def _calculate_stats(**context):                                       # @NOTE Receive all context variables in this dict
    """Calculates event statistics."""
    input_path = context["templates_dict"]["input_path"]               # @NOTE Retrieve the templated values from the templates_dict object.
    output_path = context["templates_dict"]["output_path"]

    events = pd.read_json(input_path)
    stats = events.groupby(["date", "user"]).size().reset_index()

    Path(output_path).parent.mkdir(exist_ok=True)
    stats.to_csv(output_path, index=False)


calculate_stats = PythonOperator(
    task_id="calculate_stats",
    python_callable=_calculate_stats,
    templates_dict={
        "input_path": "/opt/airflow/data/events/{{ds}}.json",     # @NOTE Pass the values that we want to be templated.
        "output_path": "/opt/airflow/data/stats/{{ds}}.csv",
    },
    provide_context=True,
    dag=dag,
)


fetch_events >> calculate_stats
