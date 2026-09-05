# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import hashlib


def _get_hex_digest(txt: str, algorithm: str = "sha1", encoding: str = "utf-8") -> str:
    hash_fn = hashlib.sha1
    if algorithm == "sha256":
        hash_fn = hashlib.sha256

    return hash_fn(txt.encode(encoding)).hexdigest()


def get_upload_channel(
    upload_id: str,
    user_id: str,
) -> str:

    return _get_hex_digest(
        txt=f"file_upload::{upload_id}::{user_id}",
        algorithm="sha256",
    )
