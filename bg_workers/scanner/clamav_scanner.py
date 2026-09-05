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
