# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

from celery import Celery

from app.config.config import Settings

celery_client = Celery(
    "eurekai-api", broker=Settings.BROKER_URL, backend=Settings.BACKEND_URL
)

celery_client.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json"
)
