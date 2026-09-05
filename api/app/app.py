# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import Settings
from app.db.redis_db import close_redis, get_redis, init_redis
from app.v1.router.upload import router as upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    r = get_redis()

    yield

    await close_redis()


origins = Settings.CORS_ORIGIN.split(",")

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=Settings.CORS_ALLOWED_METHODS.split(","),
    allow_headers=["*"],
)


app.include_router(upload_router, prefix="/v1", tags=["upload"])


@app.get("/health")
async def get_health():
    return {"message": "I'm live", "statusCode": 200}
