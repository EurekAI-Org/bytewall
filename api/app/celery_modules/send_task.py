# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import uuid
from typing import Any

from shared.celery_queues.task_queues import TASK_QUEUES

from app.celery_modules.celery_client import celery_client


def send_task(*, task_name: str, task_data: Any):
    """
    Sends tasks to celery app workers.
    """
    assert task_name.startswith(
        "tasks."
    ), f"task_name should start with 'tasks.'. Received task_name={task_name}"

    task_id = task_data.get("task_id", uuid.uuid4().hex)
    queue = TASK_QUEUES.get(task_name, {}).get("queue", "celery")
    print("CELERY QUEUE used: ", queue)
    celery_client.send_task(
        name=task_name, kwargs=task_data, task_id=task_id, queue=queue
    )

    return task_id
