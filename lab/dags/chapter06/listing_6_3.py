import airflow.utils.dates
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator

dag = DAG(
    dag_id="06_listing_6_3",
    start_date=airflow.utils.dates.days_ago(3),
    schedule_interval="@daily",
    concurrency=50,
)

DummyOperator(task_id="dummy", dag=dag)
