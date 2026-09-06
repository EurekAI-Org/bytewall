# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright (c) 2026 EurekAI Pvt. Ltd.
# SPDX-License-Identifier: MIT
#

import mimetypes
import pathlib
import unicodedata

import magic
from fastapi import UploadFile

from app.utility.utils import ACTUAL_MIME_TYPES

mimetypes.init()

MAX_FILENAME_CHARS = 150
MAX_FILENAME_BYTES = 255


class FileValidator:
    def __init__(self, allowed_types: str, max_file_sizes: dict[str, int]):
        self.__max_file_sizes = {
            ext.lower(): 1024 * 1024 * size for ext, size in max_file_sizes.items()
        }
        self.__allowed_mime_types, self.__allowed_extensions = self.__get_allowed_types(
            allowed_types
        )

        # print(self.__allowed_mime_types)
        # print(self.__allowed_extensions)

    def __get_allowed_types(
        self, allowed_types: str
    ) -> tuple[frozenset[str] | None, frozenset[str] | None]:

        if allowed_types.strip() == "*":
            return None, None

        allowed_mime_types: set[str] = set()
        allowed_extensions: set[str] = set()

        for raw_ext in allowed_types.split(","):
            ext = raw_ext.strip().lower()

            if not ext:
                continue

            if not ext.startswith("."):
                ext = f".{ext}"

            mime_type = self.__guess_mime_type(f"upload{ext}")

            if mime_type is None:
                raise ValueError(f"Unknown or unsupported file extension: {ext}")

            allowed_mime_types.add(mime_type)
            allowed_extensions.add(ext)

        if not allowed_mime_types:
            raise ValueError("No valid allowed file types were provided")

        return frozenset(allowed_mime_types), frozenset(allowed_extensions)

    def __guess_mime_type(self, filename: str) -> str | None:
        guess_file_type = getattr(mimetypes, "guess_file_type", None)

        if guess_file_type is not None:
            mime_type, _ = guess_file_type(filename, strict=False)
        else:
            mime_type, _ = mimetypes.guess_type(filename, strict=False)

        return mime_type.lower() if mime_type else None

    def __has_multiple_extension(self, filename: str) -> bool:
        extn_len = len([x.lower() for x in filename.split(".")[1:]])
        return extn_len > 1

    def __has_null_byte(self, filename: str) -> bool:
        """Null-byte injection check"""
        return "\x00" in filename or "%00" in filename.lower()

    def __is_filename_too_long(self, filename: str) -> bool:
        normalized_fn = unicodedata.normalize("NFC", filename)
        return (
            len(normalized_fn) > MAX_FILENAME_CHARS
            or len(normalized_fn.encode("utf-8")) > MAX_FILENAME_BYTES
        )

    def __validate_extension(self, filename: str) -> str | None:
        if self.__allowed_extensions is None:
            return

        ext = pathlib.Path(filename).suffix.lower()
        if not ext:
            return "File does not have an extension"

        if ext not in self.__allowed_extensions:
            return f"File extension {ext} is not allowed"

    def __declared_mime_type(self, file: UploadFile) -> str | None:
        return (
            file.content_type.split(";", maxsplit=1)[0].strip().lower()
            if file.content_type
            else None
        )

    def __validate_declared_mime_type(
        self, file: UploadFile, filename: str
    ) -> str | None:

        if self.__allowed_mime_types is None:
            return

        filename_mime_type = self.__guess_mime_type(filename)

        if filename_mime_type is None:
            return "Unable to determine MIME type from filename"

        if filename_mime_type not in self.__allowed_mime_types:
            return f"File type: '{filename_mime_type}' is not allowed"

        # declared_mime_type = (
        #     file.content_type.split(";", maxsplit=1)[0].strip().lower()
        #     if file.content_type
        #     else None
        # )

        declared_mime_type = self.__declared_mime_type(file=file)

        if (
            declared_mime_type
            and declared_mime_type != "application/octet-stream"
            and declared_mime_type != filename_mime_type
        ):
            return (
                "Declared MIME type does not match the filename: "
                f"declared='{declared_mime_type}', "
                f"expected='{filename_mime_type}'"
            )

    def __detect_actual_mime_type(self, content: bytes) -> str:
        return magic.from_buffer(content[:8192], mime=True)

    def __validate_actual_mime_type(self, filename: str, content: bytes) -> str | None:

        ext = pathlib.Path(filename).suffix.lower()
        allowed_actual_mimes = ACTUAL_MIME_TYPES.get(ext)

        if allowed_actual_mimes is None:
            return f"No file signature policy configured for extension '{ext}'"

        actual_mime = self.__detect_actual_mime_type(content=content)
        if actual_mime not in allowed_actual_mimes:
            return f"File content does not match its extension - extension: {ext}, detected: {actual_mime}"

    async def validate_file(self, file: UploadFile) -> dict:

        if not file.filename or file.filename.strip() == "":
            return {"valid": False, "error": "No file selected"}

        filename = unicodedata.normalize("NFC", file.filename.strip())

        # ------------------------------------------------
        # FILENAME VALIDATION
        # --------------------------------------------------

        # *****************************************
        #   1. Null Byte Injection Check
        # *****************************************
        if self.__has_null_byte(filename):
            return {"valid": False, "error": "Filename contains null byte injection"}

        # *****************************************
        #   2. Filename length check
        # *****************************************

        if self.__is_filename_too_long(filename):
            return {"valid": False, "error": "Filename is too long"}

        # *****************************************
        #   3. Filename contains Path check
        # *****************************************

        if "/" in filename or "\\" in filename:
            return {
                "valid": False,
                "error": "Filename must not contain path seperators",
            }

        # *****************************************
        #   4. Filename has multiple extensions
        # *****************************************

        if self.__has_multiple_extension(filename):
            return {"valid": False, "error": "Multiple extension file provided"}

        # -----------------------------------------------
        # Extension allowlist
        # -----------------------------------------------
        ext_err = self.__validate_extension(filename)

        if ext_err:
            return {"valid": False, "error": ext_err}

        # -------------------------------------------------
        # Request MIME validation
        # -------------------------------------------------

        declared_mime_type = self.__declared_mime_type(file=file)
        mime_err = self.__validate_declared_mime_type(file=file, filename=file.filename)
        if mime_err:
            return {"valid": False, "error": mime_err}

        # ---------------------------------------------------
        # Size Validation & Actual MIME Type check
        # ---------------------------------------------------

        actual_mime_type = None
        try:
            # ************************************************
            # a. File Size check
            # ************************************************
            ext = pathlib.Path(filename).suffix.lower()
            max_file_size: int = self.__max_file_sizes.get(ext, 0)
            content = await file.read(max_file_size + 1)
            file_sz = len(content)

            if not file_sz:
                return {"valid": False, "error": "Empty files are not allowed"}

            if file_sz > max_file_size:
                return {
                    "valid": False,
                    "error": f"File too large ({file_sz:,} bytes). Maximum {max_file_size:,} bytes allowed",
                }

            # ************************************************
            #  b. Actual MIME Type check
            # ************************************************
            actual_mime_type = self.__detect_actual_mime_type(content)
            actual_mime_err = self.__validate_actual_mime_type(
                filename=filename, content=content
            )
            if actual_mime_err:
                return {"valid": False, "error": actual_mime_err}

        finally:
            await file.seek(0)

        return {
            "valid": True,
            "error": "",
            "meta": {
                "name": filename,
                "extension": pathlib.Path(filename).suffix.lower(),
                "size": file_sz,
                "declared_mime_type": declared_mime_type,
                "detected_mime_type": actual_mime_type,
            },
        }
