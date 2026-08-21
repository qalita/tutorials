from datetime import datetime

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

from _lib.qalita_operator import QalitaOperator


with DAG(
    dag_id="qalita_example_dag",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["qalita", "tutorial"],
) as dag:
    extract = BashOperator(
        task_id="extract",
        bash_command="echo 'Extracting source data...'",
    )

    transform = BashOperator(
        task_id="transform",
        bash_command="echo 'Transforming data into staging...'",
    )

    # Smoke test: show CLI version via Python package
    qalita_cli_version = QalitaOperator(
        task_id="qalita_cli_version",
        command=["version"],
    )

    # Register the worker and verify connectivity
    qalita_worker_login = QalitaOperator(
        task_id="qalita_worker_login",
        command=["worker", "login"],
        env={
            "QALITA_WORKER_NAME": "airflow-worker",
            "QALITA_WORKER_MODE": "job",
            # Expected to be set via Airflow connections/variables or .env
            # QALITA_WORKER_TOKEN, QALITA_WORKER_ENDPOINT
        },
    )

    # Example one-shot job run using documented flags.
    # "job" mode runs a single job and exits, which is what a DAG task wants;
    # "worker" mode would loop waiting for work and never let the task finish.
    # Requires valid IDs; replace with your own or parameterize via Variables
    qalita_worker_run = QalitaOperator(
        task_id="qalita_worker_run",
        command=[
            "worker",
            "run",
            "-s",
            "{{ var.json.qalita_params.source_id | default('1') }}",
            "-p",
            "{{ var.json.qalita_params.pack_id | default('1') }}",
        ],
        env={
            "QALITA_WORKER_MODE": "job",
        },
    )

    # Helper commands (optional) to explore configured entities
    qalita_source_list = QalitaOperator(
        task_id="qalita_source_list",
        command=["source", "list"],
    )
    qalita_pack_list = QalitaOperator(
        task_id="qalita_pack_list",
        command=["pack", "list"],
    )

    extract >> transform >> qalita_cli_version >> qalita_worker_login
    qalita_worker_login >> [qalita_source_list, qalita_pack_list] >> qalita_worker_run
