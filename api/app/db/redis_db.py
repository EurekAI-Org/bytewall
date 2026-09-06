# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

from redis.asyncio import Redis

from app.config.config import Settings

redis: Redis | None = None


async def init_redis():
    global redis
    if redis is None:
        redis = Redis(
            host=Settings.REDIS_HOST,
            port=Settings.REDIS_PORT,
            username=Settings.REDIS_USERNAME,
            password=Settings.REDIS_PASSWORD,
            db=Settings.REDIS_DB,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )


async def close_redis():
    global redis
    if redis is not None:
        await redis.close()
        redis = None


def get_redis():
    # global redis
    if redis is None:
        raise RuntimeError("Redis not initialized")
    return redis
