# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import logging
import sys
from typing import Literal

from pythonjsonlogger.json import JsonFormatter

LVL = {
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}


def get_logger(
    name: str, log_lvl: Literal["info", "debug", "warn", "error"] = "info"
) -> logging.Logger:

    logger = logging.getLogger(name=name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(LVL[log_lvl])
        logger.propagate = False

    return logger
