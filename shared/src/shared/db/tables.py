# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import datetime
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db.models import BaseTable


class UploadedFileTable(BaseTable):
    __tablename__ = "uploaded_files"
    __table_args__ = (
        UniqueConstraint("bucket", "key", name="uq_bucket_key"),
        CheckConstraint(
            "purpose IN ('profile_pic', 'note_img', 'comment_img', 'post_img', 'attachment')"
        ),
        CheckConstraint(
            "scan_res IN ('pending', 'clean', 'suspicious', 'malicious', 'failed')",
            name="ck_uploaded_file_scan_res",
        ),
        {"schema": "app"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    purpose: Mapped[str]
    key: Mapped[str] = mapped_column(nullable=False)
    bucket: Mapped[str] = mapped_column(nullable=False)
    file_meta: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scan_res: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'pending'")
    )
    scan_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ------ Relationship ------
    job: Mapped["UploadJobTable"] = relationship(back_populates="file")


class SanitizedFileTable(BaseTable):
    __tablename__ = "sanitized_files"
    __table_args__ = (
        UniqueConstraint("bucket", "key", name="uq_bucket_key_sanitized"),
        {"schema": "app"},
    )

    uploaded_file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app.uploaded_files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    key: Mapped[str] = mapped_column(nullable=False)
    bucket: Mapped[str] = mapped_column(nullable=False)
    file_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scan_res: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'pending'")
    )
    scan_meta: Mapped[dict] = mapped_column(JSONB, nullable=True)


class UploadJobTable(BaseTable):
    __tablename__ = "upload_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'retrying', 'failed', 'complete', 'rejected')",
            name="ck_upload_job_status",
        ),
        CheckConstraint(
            "stage IN ('download', 'scan', 'sanitize', 'post_scan', 'upload', 'cleanup')",
            name="ck_upload_job_stage",
        ),
        Index("ix_upload_jobs_retry", "status", "next_retry_at"),
        {"schema": "app"},
    )

    uploaded_file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app.uploaded_files.id"), nullable=False, index=True, unique=True
    )
    celery_task_id: Mapped[str | None]
    status: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'pending'")
    )
    stage: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'download'")
    )
    retries: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    error_type: Mapped[str | None]
    error_message: Mapped[str | None]
    next_retry_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ---------------- Relationships -----------------
    file: Mapped["UploadedFileTable"] = relationship(back_populates="job")
