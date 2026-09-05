# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict

# load_dotenv()


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    BROKER_URL: str
    BACKEND_URL: str

    POSTGRES_URL: str
    POSTGRES_CONNECTION_POOL_SIZE: int = pydantic.Field(default=5)
    POSTGRES_MAX_OVERFLOW: int = pydantic.Field(default=10)

    REDIS_URL: str

    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION_NAME: str
    S3_BUCKET_NAME: str

    CLAMAV_HOST: str
    CLAMAV_PORT: int

    MAX_TASK_RETRIES: int = pydantic.Field(default=3)


Settings = Config()  # pyright: ignore
