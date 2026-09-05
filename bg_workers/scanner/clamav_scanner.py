# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import pathlib

from clamav_client.clamd import ClamdNetworkSocket, CommunicationError

from utility.exceptions import ClamAVUnavailableError


def scan_clamav(file_path: pathlib.Path, clamav: ClamdNetworkSocket) -> dict:

    try:
        with file_path.open("rb") as file:
            res = clamav.instream(file)
    except (CommunicationError, OSError) as exc:
        raise ClamAVUnavailableError("ClamAV service unavailable") from exc

    status, signature = res["stream"]

    return {"clean": status == "OK", "signature": signature}
