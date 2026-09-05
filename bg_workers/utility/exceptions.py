# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 Adityam Ghosh (@lucifermorningstar1305). All rights reserved.
#
# This software is proprietary and confidential.
# Use, reproduction, modification, or distribution is permitted only
# as expressly authorized under a written licence or agreement
# with the copyright holder.
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
