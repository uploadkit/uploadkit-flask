"""Adapt Werkzeug / Flask uploaded files for UploadKit Core."""

from __future__ import annotations

from werkzeug.datastructures import FileStorage

from uploadkit import UploadableFile


class _FileStorageAdapter:
    """Expose Werkzeug ``FileStorage`` as sync ``UploadableFile``."""

    def __init__(self, upload_file: FileStorage) -> None:
        self._upload = upload_file

    @property
    def name(self) -> str | None:
        return self._upload.filename

    @property
    def size(self) -> int | None:
        return self._upload.content_length

    @property
    def content_type(self) -> str | None:
        return self._upload.content_type

    def read(self, size: int = -1) -> bytes:
        return self._upload.stream.read(size)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._upload.stream.seek(offset, whence)

    def tell(self) -> int:
        return self._upload.stream.tell()


def as_uploadable(file: FileStorage) -> UploadableFile:
    """Adapt Flask/Werkzeug ``FileStorage`` for sync ``Uploader``.

    Flask routes receive multipart files as Werkzeug ``FileStorage``
    objects (e.g. ``request.files["file"]``). This adapter maps them to
    Core's ``UploadableFile`` protocol — notably ``filename`` → ``name``
    (``FileStorage.name`` is the form field name).
    """
    return _FileStorageAdapter(file)
