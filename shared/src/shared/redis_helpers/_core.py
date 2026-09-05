# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

import redis
import redis.asyncio

TRANSIENT_ERR = (
    redis.ConnectionError,
    redis.TimeoutError,
    redis.asyncio.ConnectionError,
    redis.asyncio.TimeoutError,
)
T = TypeVar("T")


def is_transient_err(exc: Exception) -> bool:
    return isinstance(exc, TRANSIENT_ERR)


def with_retry(
    fn: Callable,
    *,
    max_attempts: int = 3,
    delay: float = 0.4,
    allowed: Callable = is_transient_err,
    logger: logging.Logger | None = None,
) -> T | None:

    last_err = None
    for _ in range(max_attempts):
        try:
            return fn()

        except Exception as e:
            last_err = e

            if logger is not None:
                logger.exception(f"Error executing {fn}")

            if not allowed(last_err):
                if logger is not None:
                    logger.exception(f"Error executing function {fn}: {last_err}")

                raise

            time.sleep(delay)
            delay = min(delay * 2, 2.0)

            continue

    if last_err is not None:
        if logger is not None:
            logger.exception(f"Error executing function {fn}: {last_err}")

        raise last_err


async def with_retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    delay: float = 0.4,
    allowed: Callable = is_transient_err,
    logger: logging.Logger | None = None,
) -> T | None:
    last_err = None

    for _ in range(max_attempts):
        try:
            return await fn()

        except Exception as e:
            last_err = e
            if not allowed(e):
                if logger is not None:
                    logger.exception(f"Error executing function {fn}")
                raise

            await asyncio.sleep(delay)
            delay = min(delay * 2, 2.0)
            continue

    if last_err is not None:
        if logger is not None:
            logger.exception(f"Error executing function {fn}: {last_err}")

        raise last_err
