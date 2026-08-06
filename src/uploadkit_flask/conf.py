"""Flask app.config helpers for UploadKit."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flask import current_app

from uploadkit import StorageProvider


def get_storage_provider() -> StorageProvider:
    """Resolve ``UPLOADKIT_STORAGE_PROVIDER`` from Flask ``app.config``.

    The setting must be a callable that returns a ``StorageProvider``,
    or a dotted path string to such a callable.
    """
    value: Any = current_app.config.get("UPLOADKIT_STORAGE_PROVIDER")
    if value is None:
        raise ImproperlyConfiguredUploadKit(
            "Set UPLOADKIT_STORAGE_PROVIDER to a StorageProvider factory"
        )
    if isinstance(value, str):
        from werkzeug.utils import import_string

        value = import_string(value)
    if not callable(value):
        raise ImproperlyConfiguredUploadKit(
            "UPLOADKIT_STORAGE_PROVIDER must be a callable factory"
        )
    provider = value()
    return provider


class ImproperlyConfiguredUploadKit(Exception):
    """Raised when Flask UploadKit config is missing or invalid."""


StorageFactory = Callable[[], StorageProvider]
