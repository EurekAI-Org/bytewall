# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

from typing import Literal, TypedDict


class FileMeta(TypedDict):
    size: int
    content_type: str


class ScanType(TypedDict):
    id: str
    user_id: str
    key: str
    bucket: str
    file_ext: str
    file_meta: FileMeta
    purpose: Literal["profile_pic", "note_img", "comment_img", "post_img", "attachment"]
