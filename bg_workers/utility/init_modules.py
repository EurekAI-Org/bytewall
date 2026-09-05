# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import pathlib

import boto3
import redis
import sqlalchemy
import yara
from clamav_client.clamd import ClamdNetworkSocket
from shared.logger.logger import get_logger

from config import Settings

_INIT: bool = False

YARA_RULES = None
REDIS_CLIENT = None
SQLENGINE = None
CLAMAV = None
S3_CLIENT = None


logger = get_logger("celery.workers.init")


# def _create_bucket(s3: Any):
#     try:
#         s3.create_bucket(Bucket=Settings.S3_BUCKET_NAME)
#         logger.info(f"Bucket: {Settings.S3_BUCKET_NAME}  - created")
#     except s3.exceptions.BucketAlreadyOwnedByYou:
#         logger.warning(f"Bucket '{Settings.S3_BUCKET_NAME}' already exists")
#


def init_modules():
    global _INIT, YARA_RULES, REDIS_CLIENT, SQLENGINE, CLAMAV, S3_CLIENT

    if _INIT:
        return

    _INIT = True

    yara_path = (
        pathlib.Path(__file__).parent.parent / "rules" / "upload_rules_index.yar"
    )

    if yara_path.exists():
        YARA_RULES = yara.compile(filepath=str(yara_path))
    else:
        YARA_RULES = None

    REDIS_CLIENT = redis.Redis.from_url(url=Settings.REDIS_URL, decode_responses=True)
    SQLENGINE = sqlalchemy.create_engine(
        url=Settings.POSTGRES_URL,
        pool_size=Settings.POSTGRES_CONNECTION_POOL_SIZE,
        max_overflow=Settings.POSTGRES_MAX_OVERFLOW,
        pool_pre_ping=True,
    )

    CLAMAV = ClamdNetworkSocket(
        host=Settings.CLAMAV_HOST, port=Settings.CLAMAV_PORT, timeout=60
    )
    CLAMAV.ping()

    S3_CLIENT = boto3.client(
        "s3",
        endpoint_url=Settings.S3_ENDPOINT_URL,
        aws_access_key_id=Settings.S3_ACCESS_KEY,
        aws_secret_access_key=Settings.S3_SECRET_KEY,
        region_name=Settings.S3_REGION_NAME,
    )

    # _create_bucket(s3=S3_CLIENT)
