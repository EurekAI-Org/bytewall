# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import uuid
from typing import Annotated, Literal

from app.celery_modules.send_task import send_task
from app.config.config import Settings
from app.db.db import get_session
from app.db.redis_db import get_redis
from app.services.file_validator import FileValidator
from app.services.insert_save_file_record import insert_record
from app.services.save_file import save_file
from app.services.streams import stream_file_scan_status
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from redis.asyncio import Redis
from shared.logger.logger import get_logger
from shared.typed_dicts.params import FileMeta, ScanType
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/upload", tags=["upload"])

validator = FileValidator(
    allowed_types=Settings.ALLOWED_EXTENSIONS, max_file_sizes=Settings.MAX_UPLOAD_SIZE
)

logger = get_logger("file.upload")
# create_bucket()


@router.post("/single")
async def upload_single_file(
    user_id: Annotated[uuid.UUID, Form()],
    file: Annotated[UploadFile, File()],
    purpose: Annotated[
        Literal["profile_pic", "note_img", "comment_img", "post_img", "attachment"],
        Form(),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        res = await validator.validate_file(file=file)

        if not res["valid"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "data": None, "error": res["error"]},
            )
            # return {"message": res["error"], "statusCode": status.HTTP_400_BAD_REQUEST}

        meta = res["meta"]
        file_id = uuid.uuid4().hex
        key = f"{purpose}/{file_id}{meta['extension']}"

        await save_file(file=file, key=key, content_type=meta["detected_mime_type"])

        uploaded_file_id = await insert_record(
            user_id=user_id, purpose=purpose, key=key, file_meta=meta, session=session
        )

        send_task(
            task_name="tasks.scan_upload",
            task_data=ScanType(
                id=str(uploaded_file_id),
                user_id=str(user_id),
                key=key,
                bucket=Settings.S3_UPLOAD_BUCKET_NAME,
                file_ext=meta["extension"],
                purpose=purpose,
                file_meta=FileMeta(
                    size=meta["size"], content_type=meta["detected_mime_type"]
                ),
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": str(uploaded_file_id), "error": None},
        )
        # return {
        #     "message": "SUCCESS",
        #     "statusCode": status.HTTP_200_OK,
        #     "data": str(uploaded_file_id),
        # }

    except Exception:
        logger.exception("Failed to upload file")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "data": None, "error": "Internal Server Error"},
        )
        # return {
        #     "message": "Oops...Something went wrong",
        #     "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
        # }


@router.get("/single/{file_id}/stream")
async def get_scan_status(
    file_id: str,
    request: Request,
    user_id: uuid.UUID,
    redis_client: Annotated[Redis, Depends(get_redis)],
):
    return StreamingResponse(
        stream_file_scan_status(
            request=request,
            user_id=user_id,
            uploaded_file_id=file_id,
            redis_client=redis_client,
        )
    )
