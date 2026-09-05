# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import pathlib

import yara


def scan_yara(file_path: pathlib.Path, rules: yara.Rules) -> dict:
    matches = rules.match(str(file_path), timeout=30)
    return {"clean": len(matches) == 0, "matches": [match.rule for match in matches]}
