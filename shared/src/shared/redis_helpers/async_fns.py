# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import json
import logging
from typing import Any

from redis.asyncio import Redis

from shared.redis_helpers._core import with_retry_async


async def publish_event(redis_client: Redis, channel_name: str, event: dict[str, Any]):
    return await redis_client.publish(
        channel=channel_name, message=json.dumps(event, ensure_ascii=False)
    )


async def safe_publish_event(
    redis_client: Redis,
    channel_name: str,
    event: dict[str, Any],
    max_attempts: int = 3,
    delay: float = 0.4,
    logger: logging.Logger | None = None,
    raise_err: bool = False,
):
    try:
        return await with_retry_async(
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
