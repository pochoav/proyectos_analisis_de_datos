from datetime import datetime, timedelta
from pathlib import Path

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

#Declaración de rutas relativas
PROJECT_DIR = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_DIR / "dbt_project"
EXTRACT_SCRIPT = PROJECT_DIR / "scripts" / "extract_to_warehouse.py"

#Rutas virtuales para cada herramienta
EXTRACT_PYTHON = Path.home() / "venvs" / "extract" / "bin" / "python"
DBT_BIN = Path.home() / "venvs" / "dbt" / "bin" / "dbt"

with DAG(
    dag_id="air_quality_elt_pipeline",
    description="Open-Meteo -> BigQuery -> dbt run -> dbt test",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["proyecto_5", "elt"],
    ) as dag:

    extract_to_warehouse = BashOperator(
        task_id="extract_to_warehouse",
        bash_command=f"{EXTRACT_PYTHON} {EXTRACT_SCRIPT}",
        retries=1,
        retry_delay=timedelta(minutes=1),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && {DBT_BIN} run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && {DBT_BIN} test",
    )

    extract_to_warehouse >> dbt_run >> dbt_test