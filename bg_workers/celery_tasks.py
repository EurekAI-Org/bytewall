# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import datetime
import uuid
from typing import Unpack

import utility.init_modules as im
from celery_app import celery_app
from config import Settings
from shared.logger.logger import get_logger
from shared.redis_helpers.generate_keys import get_upload_channel
from shared.typed_dicts.params import FileMeta, ScanType
from sqlalchemy.exc import DBAPIError, OperationalError
from tasks.sanitize import sanitize_file
from tasks.scan_file import scan_file
from utility.db_ops import (
    del_record,
    fetch_reclaimable_records,
    insert_record,
    update_record,
    upsert_upload_job,
)
from utility.exceptions import (
    ClamAVUnavailableError,
    PasswordProtectedPDF,
    S3DeleteFailed,
    S3DownloadFailed,
    S3UploadFailed,
    UnsupportedExtension,
    UnsupportedImageExtension,
)
from utility.publish import publish_event
from utility.storage import (
    delete_quarantined_file,
    download_quarantined_file,
    upload_sanitized_file,
)

logger = get_logger("workers.tasks")


@celery_app.task(
    name="tasks.scan_upload", bind=True, max_retries=Settings.MAX_TASK_RETRIES
)
def scan_uploaded_file(self, **data: Unpack[ScanType]):

    assert im.SQLENGINE is not None
    assert im.CLAMAV is not None
    # assert im.YARA_RULES is not None
    assert im.S3_CLIENT is not None
    assert im.REDIS_CLIENT is not None

    file_path = None
    sanitized_path = None
    channel_name = get_upload_channel(
        upload_id=data["id"],
        user_id=data["user_id"],
    )
    healthy = False
    verdict = ""
    stage = "download"
    try:
        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="running",
            stage="download",
        )

        file_path = download_quarantined_file(**data, s3=im.S3_CLIENT)

        stage = "scan"
        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="running",
            stage=stage,
        )

        scan_res = scan_file(
            file_path=file_path,
            clamav=im.CLAMAV,
            yara_rules=im.YARA_RULES,
        )

        if scan_res["verdict"] == "malicious":
            stage = "cleanup"
            update_record(
                engine=im.SQLENGINE,
                key=data["key"],
                bucket=data["bucket"],
                scan_meta={**scan_res["meta"]},
                scan_res=scan_res["verdict"],
            )

            del_record(engine=im.SQLENGINE, key=data["key"], bucket=data["bucket"])
            delete_quarantined_file(
                key=data["key"], bucket=data["bucket"], s3=im.S3_CLIENT
            )
            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=uuid.UUID(data["id"]),
                celery_task_id=self.request.id,
                status="complete",
                stage=stage,
            )
            publish_event(
                redis_client=im.REDIS_CLIENT,
                channel_name=channel_name,
                scan_res="malicious",
                msg="file contains malicious content",
                file_meta={**data["file_meta"]},
                status="success",
                logger=logger,
            )
            return

        file_id = update_record(
            engine=im.SQLENGINE,
            key=data["key"],
            bucket=data["bucket"],
            scan_meta={**scan_res["meta"]},
            scan_res=scan_res["verdict"],
        )

        stage = "sanitize"
        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="running",
            stage=stage,
        )

        sanitized_res = sanitize_file(file_path=file_path, file_ext=data["file_ext"])
        sanitized_path = sanitized_res["path"]

        stage = "post_scan"
        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="running",
            stage="post_scan",
        )

        sanitized_scan_res = scan_file(
            file_path=sanitized_path, clamav=im.CLAMAV, yara_rules=im.YARA_RULES
        )

        verdict = sanitized_scan_res["verdict"]
        if sanitized_scan_res["verdict"] == "clean":
            healthy = True

            stage = "upload"
            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=uuid.UUID(data["id"]),
                celery_task_id=self.request.id,
                status="running",
                stage=stage,
            )

            key = f"{data['purpose']}/{sanitized_path.name}"
            upload_sanitized_file(
                file_path=sanitized_path,
                key=key,
                s3=im.S3_CLIENT,
                bucket=Settings.S3_BUCKET_NAME,
                content_type=data["file_meta"]["content_type"],
            )
            insert_record(
                engine=im.SQLENGINE,
                file_id=file_id,
                key=key,
                scan_meta={**sanitized_scan_res["meta"]},
                scan_res=sanitized_scan_res["verdict"],
                file_meta={
                    **data["file_meta"],
                    "sanitizer": sanitized_res["sanitizer"],
                    "metadata_removed": sanitized_res["metadata_removed"],
                },
            )

            stage = "cleanup"
            del_record(engine=im.SQLENGINE, key=data["key"], bucket=data["bucket"])
            delete_quarantined_file(
                key=data["key"], bucket=data["bucket"], s3=im.S3_CLIENT
            )

            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=uuid.UUID(data["id"]),
                celery_task_id=self.request.id,
                status="complete",
                stage=stage,
            )
        else:
            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=uuid.UUID(data["id"]),
                celery_task_id=self.request.id,
                status="complete",
                stage=stage,
            )

        publish_event(
            redis_client=im.REDIS_CLIENT,
            channel_name=channel_name,
            scan_res=sanitized_scan_res["verdict"],
            msg="file contains suspicious content" if not healthy else "file is safe",
            status="success",
            logger=logger,
            file_meta={**data["file_meta"]},
        )

    except S3DownloadFailed as exc:
        if self.request.retries >= Settings.MAX_TASK_RETRIES:
            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=uuid.UUID(data["id"]),
                celery_task_id=self.request.id,
                status="failed",
                stage=stage,
                error_type="S3_DOWNLOAD",
                error_msg=str(exc),
                next_retry_at=datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(seconds=30),
            )

            logger.exception(f"Maximum retries({Settings.MAX_TASK_RETRIES}) reached.")

            publish_event(
                redis_client=im.REDIS_CLIENT,
                channel_name=channel_name,
                scan_res="unknown",
                msg="failed to download",
                file_meta={**data["file_meta"]},
                status="failed",
                logger=logger,
            )

            raise
        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="retrying",
            stage=stage,
            error_type="S3_DOWNLOAD",
            error_msg=str(exc),
            next_retry_at=datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(seconds=30),
        )
        raise self.retry(exc=exc, countdown=30)

    except S3UploadFailed as exc:
        if self.request.retries >= Settings.MAX_TASK_RETRIES:
            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=uuid.UUID(data["id"]),
                celery_task_id=self.request.id,
                status="failed",
                stage=stage,
                error_type="S3_UPLOAD",
                error_msg=str(exc),
                next_retry_at=datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(seconds=30),
            )

            logger.exception(f"Maximum retries({Settings.MAX_TASK_RETRIES}) reached.")

            publish_event(
                redis_client=im.REDIS_CLIENT,
                channel_name=channel_name,
                scan_res=verdict,
                msg="failed to upload",
                file_meta={**data["file_meta"]},
                status="failed",
                logger=logger,
            )

            raise

        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="retrying",
            stage=stage,
            error_type="S3_UPLOAD",
            error_msg=str(exc),
            next_retry_at=datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(seconds=30),
        )

        raise self.retry(exc=exc, countdown=30)

    except S3DeleteFailed as exc:
        if self.request.retries >= Settings.MAX_TASK_RETRIES:
            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=uuid.UUID(data["id"]),
                celery_task_id=self.request.id,
                status="failed",
                stage=stage,
                error_type="S3_CLEANUP",
                error_msg=str(exc),
                next_retry_at=datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(seconds=30),
            )

            logger.exception(f"Maximum retries({Settings.MAX_TASK_RETRIES}) reached.")

            publish_event(
                redis_client=im.REDIS_CLIENT,
                channel_name=channel_name,
                scan_res=verdict,
                msg="failed to cleanup",
                file_meta={**data["file_meta"]},
                status="failed",
                logger=logger,
            )

            raise

        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="retrying",
            stage=stage,
            error_type="S3_CLEANUP",
            error_msg=str(exc),
            next_retry_at=datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(seconds=30),
        )

        raise self.retry(exc=exc, countdown=30)

    except ClamAVUnavailableError as exc:
        if self.request.retries >= Settings.MAX_TASK_RETRIES:
            update_record(
                engine=im.SQLENGINE,
                scan_meta={"clamav": {"error": str(exc)}},
                scan_res="failed",
                **data,
            )
            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=uuid.UUID(data["id"]),
                celery_task_id=self.request.id,
                status="failed",
                stage=stage,
                error_type="CLAMAV_UNAVAIBLE",
                error_msg=str(exc),
                next_retry_at=datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(seconds=30),
            )

            logger.exception(f"Maximum retries({Settings.MAX_TASK_RETRIES}) reached.")

            publish_event(
                redis_client=im.REDIS_CLIENT,
                channel_name=channel_name,
                scan_res="unknown",
                msg="failed to scan the contents",
                file_meta={**data["file_meta"]},
                status="failed",
                logger=logger,
            )

            raise

        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="retrying",
            stage=stage,
            error_type="CLAMAV_UNAVAILABLE",
            error_msg=str(exc),
            next_retry_at=datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(seconds=30),
        )

        raise self.retry(exc=exc, countdown=30)

    except PasswordProtectedPDF:
        logger.error("Detected Password Protected PDF")

        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="rejected",
            stage=stage,
        )

        publish_event(
            redis_client=im.REDIS_CLIENT,
            channel_name=channel_name,
            scan_res="unknown",
            msg="unsupported pdf format provided",
            file_meta={**data["file_meta"]},
            status="failed",
            logger=logger,
        )

        raise

    except UnsupportedExtension:
        logger.error("Unsupported extension")

        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="rejected",
            stage=stage,
        )

        publish_event(
            redis_client=im.REDIS_CLIENT,
            channel_name=channel_name,
            scan_res="unknown",
            msg="unsupported file provided",
            file_meta={**data["file_meta"]},
            status="failed",
            logger=logger,
        )

        raise

    except UnsupportedImageExtension:
        logger.error("Unsupported Image extension")

        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="rejected",
            stage=stage,
        )

        publish_event(
            redis_client=im.REDIS_CLIENT,
            channel_name=channel_name,
            scan_res="unknown",
            msg="unsupported image provided",
            file_meta={**data["file_meta"]},
            status="failed",
            logger=logger,
        )

        raise

    except (DBAPIError, OperationalError) as exc:
        logger.exception("PostgreSQL unavailable")

        if self.request.retries >= Settings.MAX_TASK_RETRIES:
            logger.error(
                f"PostgreSQL unavailable after {Settings.MAX_TASK_RETRIES} retries"
            )
            raise

        raise self.retry(exc=exc, countdown=30)

    except Exception as exc:
        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=uuid.UUID(data["id"]),
            celery_task_id=self.request.id,
            status="failed",
            stage=stage,
            error_type="UNKNOWN_ERROR",
            error_msg=str(exc),
            next_retry_at=datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(seconds=30),
        )

        publish_event(
            redis_client=im.REDIS_CLIENT,
            channel_name=channel_name,
            scan_res="unknown",
            msg="scan failed",
            file_meta={**data["file_meta"]},
            status="failed",
            logger=logger,
        )

        raise

    finally:
        if sanitized_path is not None:
            sanitized_path.unlink(missing_ok=True)

        if file_path is not None:
            file_path.unlink(missing_ok=True)


@celery_app.task(
    name="tasks.rerun_file_uploads", bind=True, max_retries=Settings.MAX_TASK_RETRIES
)
def rerun_uploads(self):
    assert im.SQLENGINE is not None

    rows = fetch_reclaimable_records(engine=im.SQLENGINE)

    for row in rows:
        scan_data = ScanType(
            id=str(row.uploaded_file_id),
            user_id=str(row.user_id),
            key=row.key,
            bucket=row.bucket,
            file_ext="." + row.key.split("/")[-1].split(".")[-1].lower(),
            file_meta=FileMeta(
                size=row.file_meta.get("size", 0),
                content_type=row.file_meta.get("detected_mime_type"),
            ),
            purpose=row.purpose,
        )

        task_id = uuid.uuid4().hex
        upsert_upload_job(
            engine=im.SQLENGINE,
            uploaded_file_id=row.uploaded_file_id,
            celery_task_id=task_id,
            status="retrying",
            stage=row.stage,
        )

        try:
            celery_app.send_task(
                "tasks.scan_upload", kwargs=dict(scan_data), task_id=task_id
            )

        except Exception as exc:
            upsert_upload_job(
                engine=im.SQLENGINE,
                uploaded_file_id=row.uploaded_file_id,
                celery_task_id=task_id,
                status="failed",
                stage=row.stage,
                error_type="CELERY_DISPATCH_FAILED",
                error_msg=str(exc),
                next_retry_at=datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(seconds=30),
            )

            logger.exception(f"Failed to re-dispatch upload {row.uploaded_file_id!s}")
            continue
