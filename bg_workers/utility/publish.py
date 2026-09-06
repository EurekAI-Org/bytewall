# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import logging
from typing import Literal

from redis import Redis
from shared.redis_helpers.sync_fns import safe_publish_event


def publish_event(
    *,
    redis_client: Redis,
    channel_name: str,
    scan_res: str,
    msg: str,
    file_meta: dict,
    status: Literal["success", "failed"] = "success",
    logger: logging.Logger | None = None,
):
    safe_publish_event(
        redis_client=redis_client,
        channel_name=channel_name,
        event={
            "status": status,
            "scan_result": scan_res,
            "file_meta": {
                "size": file_meta["size"],
                "content-type": file_meta["content_type"],
            },
            "message": msg,
        },
        logger=logger,
    )
