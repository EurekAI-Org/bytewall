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
from typing import Literal, TypedDict


class ScanMeta(TypedDict):
    yara: dict
    clamav: dict


class ScanRes(TypedDict):
    verdict: Literal["clean", "suspicious", "failed", "malicious"]
    meta: ScanMeta


class SanitizerRes(TypedDict):
    path: pathlib.Path
    sanitizer: Literal["pymupdf", "pillow"]
    metadata_removed: bool
