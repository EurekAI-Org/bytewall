# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import datetime
import uuid
from collections.abc import Sequence
from typing import Literal

import sqlalchemy
from shared.db.tables import SanitizedFileTable, UploadedFileTable, UploadJobTable
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from config import Settings


def update_record(
    *,
    engine: sqlalchemy.Engine,
    key: str,
    bucket: str,
    scan_meta: dict,
    scan_res: Literal["malicious", "clean", "failed", "suspicious"],
    **kwargs,
) -> uuid.UUID:
    with Session(engine) as session:
        stmt = (
            sqlalchemy.update(UploadedFileTable)
            .where(UploadedFileTable.bucket == bucket, UploadedFileTable.key == key)
            .values({"scan_meta": scan_meta, "scan_res": scan_res})
        ).returning(UploadedFileTable.id)

        res = session.execute(stmt).one()
        session.commit()

    return res.id


def del_record(*, engine: sqlalchemy.Engine, key: str, bucket: str):
    with Session(engine) as session:
        stmt = (
            sqlalchemy.update(UploadedFileTable)
            .where(UploadedFileTable.bucket == bucket, UploadedFileTable.key == key)
            .values({"deleted_at": datetime.datetime.now(tz=datetime.UTC)})
        )
        session.execute(stmt)
        session.commit()


def insert_record(
    *,
    engine: sqlalchemy.Engine,
    file_id: uuid.UUID,
    key: str,
    scan_meta: dict,
    file_meta: dict,
    scan_res: str,
):
    with Session(engine) as session:
        stmt = pg_insert(SanitizedFileTable).values(
            {
                "uploaded_file_id": file_id,
                "key": key,
                "bucket": Settings.S3_BUCKET_NAME,
                "scan_meta": scan_meta,
                "file_meta": file_meta,
                "scan_res": scan_res,
            }
        )
        session.execute(stmt)
        session.commit()


def upsert_upload_job(
    *,
    engine: sqlalchemy.Engine,
    uploaded_file_id: uuid.UUID,
    celery_task_id: str | None,
    status: Literal["running", "retrying", "failed", "complete", "rejected"],
    stage: Literal["download", "scan", "sanitize", "post_scan", "upload", "cleanup"],
    retries: int = 0,
    error_type: str | None = None,
    error_msg: str | None = None,
    next_retry_at: datetime.datetime | None = None,
):
    with Session(engine) as session:
        stmt = pg_insert(UploadJobTable).values(
            {
                "uploaded_file_id": uploaded_file_id,
                "celery_task_id": celery_task_id,
                "status": status,
                "stage": stage,
                "retries": retries,
                "error_type": error_type,
                "error_message": error_msg,
                "next_retry_at": next_retry_at,
            }
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[UploadJobTable.uploaded_file_id],
            set_={
                "celery_task_id": stmt.excluded.celery_task_id,
                "status": stmt.excluded.status,
                "stage": stmt.excluded.stage,
                "retries": stmt.excluded.retries,
                "error_type": stmt.excluded.error_type,
                "error_message": stmt.excluded.error_message,
                "next_retry_at": stmt.excluded.next_retry_at,
                "updated_at": sqlalchemy.func.now(),
            },
        )

        session.execute(stmt)
        session.commit()


def fetch_reclaimable_records(
    *,
    engine: sqlalchemy.Engine,
    limit: int = 100,
) -> Sequence[sqlalchemy.Row]:

    cur_time = datetime.datetime.now(tz=datetime.UTC)
    stale_before = cur_time - datetime.timedelta(minutes=10)
    with Session(engine) as session:
        stmt = (
            sqlalchemy.select(
                UploadJobTable.uploaded_file_id,
                UploadJobTable.status,
                UploadJobTable.stage,
                UploadedFileTable.bucket,
                UploadedFileTable.key,
                UploadedFileTable.file_meta,
                UploadedFileTable.user_id,
                UploadedFileTable.purpose,
            )
            .join(
                UploadedFileTable,
                UploadJobTable.uploaded_file_id == UploadedFileTable.id,
            )
            .where(
                sqlalchemy.or_(
                    sqlalchemy.and_(
                        UploadJobTable.status == "failed",
                        UploadJobTable.next_retry_at <= cur_time,
                    ),
                    sqlalchemy.and_(
                        UploadJobTable.status.in_(["running", "retrying"]),
                        UploadJobTable.updated_at <= stale_before,
                    ),
                )
            )
            .order_by(UploadJobTable.next_retry_at, UploadJobTable.uploaded_file_id)
            .limit(limit)
            .with_for_update(skip_locked=True, of=UploadJobTable)
        )

        return session.execute(stmt).all()
