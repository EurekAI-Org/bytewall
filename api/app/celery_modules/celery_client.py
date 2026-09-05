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

from app.config.config import Settings

celery_client = Celery(
    "eurekai-api", broker=Settings.BROKER_URL, backend=Settings.BACKEND_URL
)

celery_client.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json"
)
