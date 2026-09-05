# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
#

import json
import logging
from typing import Any

from redis import Redis

from shared.redis_helpers._core import with_retry


def publish_event(redis_client: Redis, channel_name: str, event: dict[str, Any]):

    res = redis_client.publish(
        channel=channel_name, message=json.dumps(event, ensure_ascii=False)
    )

    return res


def safe_publish_event(
    redis_client: Redis,
    channel_name: str,
    event: dict[str, Any],
    max_attempts: int = 3,
    delay: float = 0.4,
    logger: logging.Logger | None = None,
    raise_err: bool = False,
):

    try:
        return with_retry(
            lambda: publish_event(
                redis_client=redis_client, channel_name=channel_name, event=event
            ),
            max_attempts=max_attempts,
            delay=delay,
            logger=logger,
        )
    except Exception:
        if raise_err:
            raise
