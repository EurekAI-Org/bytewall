# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#


class ClamAVUnavailableError(Exception):
    pass


class UnsupportedExtension(Exception):
    pass


class UnsupportedImageExtension(Exception):
    pass


class PasswordProtectedPDF(Exception):
    pass


class S3DownloadFailed(Exception):
    pass


class S3UploadFailed(Exception):
    pass


class S3DeleteFailed(Exception):
    pass
