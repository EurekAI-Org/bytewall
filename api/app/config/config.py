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
    CORS_ORIGIN: str = pydantic.Field(default="*")
    CORS_ALLOWED_METHODS: str = pydantic.Field(default="*")
    ALLOWED_EXTENSIONS: str = pydantic.Field(default="*")
    MAX_UPLOAD_SIZE: dict[str, int] = pydantic.Field(
        default={
            ".pdf": 25,
            ".jpg": 10,
            ".jpeg": 10,
            ".png": 10,
        }
    )
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION_NAME: str
    S3_UPLOAD_BUCKET_NAME: str
    S3_SANITIZED_BUCKET_NAME: str

    POSTGRES_URL: str
    ASYNC_POSTGRES_URL: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_USERNAME: str
    REDIS_PASSWORD: str

    BROKER_URL: str
    BACKEND_URL: str


Settings = Config()  # pyright: ignore
