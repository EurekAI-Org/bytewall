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

import boto3
from botocore.client import Config
from fastapi import UploadFile
from shared.logger.logger import get_logger

from app.config.config import Settings

logger = get_logger("upload.s3")


s3 = boto3.client(
    "s3",
    endpoint_url=Settings.S3_ENDPOINT_URL,
    aws_access_key_id=Settings.S3_ACCESS_KEY,
    aws_secret_access_key=Settings.S3_SECRET_KEY,
    region_name=Settings.S3_REGION_NAME,
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)


# def create_bucket():
#     try:
#         s3.create_bucket(Bucket=Settings.S3_BUCKET_NAME)
#         logger.info("Bucket: quarantine - created")
#     except s3.exceptions.BucketAlreadyOwnedByYou:
#         logger.warning(f"Bucket '{Settings.S3_BUCKET_NAME}' already exists")
#


async def save_file(file: UploadFile, key: str, content_type: str):
    await file.seek(0)

    try:
        await asyncio.to_thread(
            s3.put_object,
            Bucket=Settings.S3_UPLOAD_BUCKET_NAME,
            Key=key,
            Body=file.file,
            ContentType=content_type,
        )
    finally:
        if not file.file.closed:
            await file.seek(0)
