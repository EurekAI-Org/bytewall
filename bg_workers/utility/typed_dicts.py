# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
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
