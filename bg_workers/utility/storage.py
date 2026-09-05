# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
#

import pathlib
import tempfile
from typing import Any

from utility.exceptions import S3DeleteFailed, S3DownloadFailed, S3UploadFailed


def download_quarantined_file(
    *, key: str, bucket: str, s3: Any, **kwargs
) -> pathlib.Path:
    suffix = pathlib.Path(key).suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        path = pathlib.Path(tmp.name)

    try:
        s3.download_file(bucket, key, str(path))
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise S3DownloadFailed(f"Failed to download file from {bucket} {key}") from exc

    return path


def upload_sanitized_file(
    *, file_path: pathlib.Path, key: str, s3: Any, content_type: str, bucket: str
):

    try:
        s3.upload_file(
            str(file_path), bucket, key, ExtraArgs={"ContentType": content_type}
        )
    except Exception as exc:
        raise S3UploadFailed(f"Failed to upload file to {bucket} {key}") from exc


def delete_quarantined_file(*, key: str, bucket: str, s3: Any):
    try:
        s3.delete_object(Bucket=bucket, Key=key)
    except Exception as exc:
        raise S3DeleteFailed(f"Failed to delete object from {bucket} {key}") from exc
