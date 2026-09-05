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
import uuid

import numpy as np
import pymupdf
from PIL import Image, ImageOps

from utility.exceptions import (
    PasswordProtectedPDF,
    UnsupportedExtension,
    UnsupportedImageExtension,
)
from utility.typed_dicts import SanitizerRes

IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}


def sanitize_image(file_path: pathlib.Path, file_ext: str) -> pathlib.Path:

    file_ext = file_ext.lower()

    if file_ext not in IMAGE_FORMATS:
        raise UnsupportedImageExtension(f"Unsupported image type: {file_ext}")

    out_path = file_path.with_name(f"{uuid.uuid4().hex}{file_ext}")

    with Image.open(file_path) as img:
        img.load()

        img = ImageOps.exif_transpose(img)

        if file_ext in {".jpg", ".jpeg"}:
            img = img.convert("RGB")
        else:
            img = img.convert("RGBA")

        pixels = np.array(img)

        rgb = pixels[:, :, :3]  # only modify RGB channels - never alpha

        rng = np.random.default_rng()
        noise = rng.integers(0, 2, size=rgb.shape, dtype=np.uint8)

        rgb ^= noise  # XOR operation to flip the lowest bit

        pixels[:, :, :3] = rgb

        clean_img = Image.fromarray(pixels, mode=img.mode)

        if file_ext in {".jpg", ".jpeg"}:
            clean_img.save(out_path, format="JPEG", quality=95, optimize=True)

        else:
            clean_img.save(out_path, format="PNG", optimize=True)

    return out_path


def sanitize_pdf(file_path: pathlib.Path) -> pathlib.Path:

    out_path = file_path.with_name(f"{uuid.uuid4().hex}.pdf")

    with pymupdf.open(file_path) as doc:
        if doc.needs_pass:
            raise PasswordProtectedPDF("Encrypted PDFs are not supported")

        # Flatten annotations / form widgets
        doc.bake(annots=True, widgets=True)

        doc.scrub(
            attached_files=True,
            embedded_files=True,
            javascript=True,
            metadata=True,
            xml_metadata=True,
            thumbnails=True,
            clean_pages=True,
            # OCR / invisible searchable txt
            hidden_text=True,
            remove_links=True,
            reset_fields=True,
            reset_responses=True,
            # Don't automatically apply user-created redactions
            redactions=False,
        )

        doc.save(out_path, garbage=4, clean=True, deflate=True)

    return out_path


def sanitize_file(file_path: pathlib.Path, file_ext: str) -> SanitizerRes:

    if file_ext.lower() in IMAGE_FORMATS:
        # return {
        #     "path": sanitize_image(file_path=file_path, file_ext=file_ext),
        #     "sanitizer": "pillow",
        #     "metadata_removed": True,
        # }

        return SanitizerRes(
            path=sanitize_image(file_path=file_path, file_ext=file_ext),
            sanitizer="pillow",
            metadata_removed=True,
        )

    if file_ext.lower() == ".pdf":
        # return {
        #     "path": sanitize_pdf(file_path=file_path),
        #     "sanitized": "pymupdf",
        #     "metadata_removed": True,
        # }

        return SanitizerRes(
            path=sanitize_pdf(file_path=file_path),
            sanitizer="pymupdf",
            metadata_removed=True,
        )

    raise UnsupportedExtension(f"Unsupported file extension provided: {file_ext}")
