# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
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
