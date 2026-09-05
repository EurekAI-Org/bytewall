# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
#

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun, worker_process_init
from kombu import Queue
from shared.celery_queues.task_queues import TASK_QUEUES
from shared.logger.logger import get_logger

from config import Settings
from utility.init_modules import init_modules

celery_app = Celery(
    "fileupload-workers",
    broker=Settings.BROKER_URL,
    backend=Settings.BACKEND_URL,
    broker_connection_retry_on_startup=True,
)

logger = get_logger("upload.workers")

celery_app.conf.update(
    include=["celery_tasks"], task_serializer="json", accept_content=["json"]
)

celery_app.conf.task_queues = (
    Queue("default", routing_key="default"),
    Queue("scan", routing_key="scan"),
    Queue("beat", routing_key="beat"),
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_routing_key = "default"  # pyright: ignore

celery_app.conf.task_routes = TASK_QUEUES

celery_app.conf.beat_schedule = {
    "rerun-reclamiable-or-failed-jobs": {
        "task": "tasks.rerun_file_uploads",
        "schedule": 300.0,  # every 5 minutes
        "options": {"queue": "beat"},
    }
}


@worker_process_init.connect
def _on_worker_process_init(**kwargs):
    init_modules()


@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    logger.info("Task started", extra={"task_id": task_id, "task_name": task.name})


@task_postrun.connect
def task_postrun_handler(task_id, task, retval, state, *args, **kwargs):
    logger.info(
        "Task completed",
        extra={"task_id": task_id, "task_name": task.name, "state": state},
    )


@task_failure.connect
def task_failure_handler(task_id, exception, traceback, *args, **kwargs):
    logger.error("Task failed", extra={"task_id": task_id, "exception": str(exception)})


if __name__ == "__main__":
    celery_app.start()
