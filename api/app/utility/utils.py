# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
#

ACTUAL_MIME_TYPES: dict[str, set[str]] = {
    ".pdf": {
        "application/pdf",
    },
    ".txt": {
        "text/plain",
    },
    ".csv": {
        "text/plain",
        "text/csv",
    },
    ".jpg": {
        "image/jpeg",
    },
    ".jpeg": {
        "image/jpeg",
    },
    ".png": {
        "image/png",
    },
    ".gif": {
        "image/gif",
    },
    # OOXML documents are ZIP containers internally.
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    },
    ".pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
    },
    # Legacy Office
    ".doc": {
        "application/msword",
        "application/x-ole-storage",
    },
    ".xls": {
        "application/vnd.ms-excel",
        "application/x-ole-storage",
    },
    ".ppt": {
        "application/vnd.ms-powerpoint",
        "application/x-ole-storage",
    },
}
