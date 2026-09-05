# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import pathlib

import yara
from clamav_client.clamd import ClamdNetworkSocket
from shared.logger.logger import get_logger

from scanner.clamav_scanner import scan_clamav
from scanner.yara_scanner import scan_yara
from utility.typed_dicts import ScanMeta, ScanRes

logger = get_logger("file.scan")


def scan_file(
    *,
    file_path: pathlib.Path,
    clamav: ClamdNetworkSocket,
    yara_rules: yara.Rules | None,
) -> ScanRes:
    clamav_res = scan_clamav(file_path=file_path, clamav=clamav)

    if yara_rules is not None:
        yara_res = scan_yara(file_path=file_path, rules=yara_rules)
    else:
        yara_res = {"clean": True}

    scan_meta = {
        "clamav": clamav_res,
        "yara": yara_res,
    }

    scan_res = None

    logger.info(f"CLAMAV RES: {clamav_res}")
    logger.info(f"YARA RES: {yara_res}")

    if not clamav_res["clean"]:
        scan_res = "malicious"
    elif not yara_res["clean"]:
        scan_res = "suspicious"
    else:
        scan_res = "clean"

    return ScanRes(verdict=scan_res, meta=ScanMeta(**scan_meta))
