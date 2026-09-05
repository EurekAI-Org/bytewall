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

import yara


def scan_yara(file_path: pathlib.Path, rules: yara.Rules) -> dict:
    matches = rules.match(str(file_path), timeout=30)
    return {"clean": len(matches) == 0, "matches": [match.rule for match in matches]}
