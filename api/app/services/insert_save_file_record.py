# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
#

import uuid

from shared.db.tables import UploadedFileTable
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config import Settings


async def insert_record(
    user_id: uuid.UUID, purpose: str, key: str, file_meta: dict, session: AsyncSession
):
    stmt = (
        pg_insert(UploadedFileTable)
        .values(
            {
                "user_id": user_id,
                "purpose": purpose,
                "key": key,
                "bucket": Settings.S3_UPLOAD_BUCKET_NAME,
                "file_meta": file_meta,
                "scan_res": "pending",
            }
        )
        .returning(UploadedFileTable.id)
    )

    res = (await session.execute(stmt)).one()
    await session.flush()

    return res.id
