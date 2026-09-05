# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
#

import asyncio
import json
import uuid

from fastapi import Request
from redis.asyncio import Redis
from shared.logger.logger import get_logger
from shared.redis_helpers.generate_keys import get_upload_channel

_LOGGER = get_logger("upload.streams")


async def stream_file_scan_status(
    request: Request, user_id: uuid.UUID, uploaded_file_id: str, redis_client: Redis
):
    channel_name = get_upload_channel(upload_id=uploaded_file_id, user_id=str(user_id))
    pubsub = redis_client.pubsub()

    await pubsub.subscribe(channel_name)

    timeout = 60
    elapsed = 0

    try:
        while elapsed < timeout:
            if await request.is_disconnected():
                break

            msg = await pubsub.get_message(ignore_subscribe_messages=True)
            # print(f">>> RAW Message: {msg}")

            if msg and msg["type"] == "message":
                data = json.loads(msg["data"])
                if data["status"] == "success":
                    yield f"data: {json.dumps({'message': data['scan_result'], 'status': 'success'})}\n\n"
                    yield "event: close\n\n"
                    break

                elif data["status"] == "failed":
                    yield f"data: {json.dumps({'message': data['scan_result'], 'status': 'failed'})}\n\n"
                    yield "event: close\n\n"
                    break

            else:
                yield ": ping\n\n"

            await asyncio.sleep(0.1)
            elapsed += 0.1
        else:
            yield f"data: {json.dumps({'status': 'timeout'})}\n\n"
            yield "event: close\n\n"

    except Exception:
        _LOGGER.exception("Stream failed")
        yield f"data: {json.dumps({'status': 'error', 'message': 'Stream failed'})}\n\n"
        yield "event: close\n\n"

    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
