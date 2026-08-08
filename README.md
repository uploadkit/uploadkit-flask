# uploadkit-flask

[![CI](https://github.com/uploadkit/uploadkit-flask/actions/workflows/ci.yml/badge.svg)](https://github.com/uploadkit/uploadkit-flask/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/uploadkit/uploadkit-flask/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](pyproject.toml)
[![Flask](https://img.shields.io/badge/flask-3.0%2B-black)](pyproject.toml)

Flask integration for UploadKit.

## What problem does this solve?

Adapts Werkzeug/`FileStorage` uploads from Flask routes and maps UploadKit exceptions to JSON responses — without reimplementing validation or storage.

## When to use it

Use when your Flask app uploads files through UploadKit Core.

## When not to use it

Do not put validators, policies, or storage implementations in this package. Supply your own `StorageProvider` (e.g. boto3 → AWS S3 or MinIO).

## Installation

Requires **Python 3.10+** and **Flask 3.0+**.

```bash
pip install uploadkit-flask uploadkit-security
```

```bash
uv add uploadkit-flask uploadkit-security
```

```bash
poetry add uploadkit-flask uploadkit-security
```

For S3/MinIO samples: `pip install boto3`.

## Storage provider (AWS S3 or MinIO)

Same class for both backends — omit `endpoint_url` for AWS, set it for MinIO:

```python
# myapp/storage.py
import boto3
from botocore.client import Config
from flask import current_app


class Boto3S3Storage:
    def __init__(
        self,
        *,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
    ) -> None:
        kwargs: dict = {
            "service_name": "s3",
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region,
            "config": Config(signature_version="s3v4"),
        }
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.client = boto3.client(**kwargs)

    def put(self, *, bucket, object_name, body, content_type):
        resp = self.client.put_object(
            Bucket=bucket,
            Key=object_name,
            Body=body,
            ContentType=content_type,
        )
        return resp.get("ETag")


def get_provider():
    """Factory used by UPLOADKIT_STORAGE_PROVIDER."""
    return Boto3S3Storage(
        access_key=current_app.config["AWS_ACCESS_KEY_ID"],
        secret_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
        region=current_app.config.get("AWS_S3_REGION_NAME", "us-east-1"),
        endpoint_url=current_app.config.get("AWS_S3_ENDPOINT_URL"),
    )
```

**AWS S3** (`app.config`):

```python
app.config["AWS_ACCESS_KEY_ID"] = "AKIA..."
app.config["AWS_SECRET_ACCESS_KEY"] = "..."
app.config["AWS_S3_REGION_NAME"] = "eu-west-1"
# AWS_S3_ENDPOINT_URL unset → real AWS
app.config["UPLOADKIT_STORAGE_PROVIDER"] = "myapp.storage.get_provider"
app.config["UPLOADKIT_BUCKET"] = "my-prod-bucket"
```

**MinIO** (`app.config`):

```python
app.config["AWS_ACCESS_KEY_ID"] = "minioadmin"
app.config["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
app.config["AWS_S3_REGION_NAME"] = "us-east-1"
app.config["AWS_S3_ENDPOINT_URL"] = "http://127.0.0.1:9000"
app.config["UPLOADKIT_STORAGE_PROVIDER"] = "myapp.storage.get_provider"
app.config["UPLOADKIT_BUCKET"] = "uploads"
```

## Quick Start (route)

```python
# myapp/views.py
from flask import current_app, jsonify, request
from uploadkit import Uploader, UploadPolicy, UploaderError
from uploadkit_flask import as_uploadable, get_storage_provider, json_error_response
from uploadkit_security import default_validators


def notify(result):
    ...


@app.post("/upload")
def upload_view():
    storage = get_storage_provider()  # Boto3S3Storage for AWS or MinIO
    policy = UploadPolicy(
        max_size=5 * 1024 * 1024,
        allowed_extensions=frozenset({"png"}),
        allowed_mime_types=frozenset({"image/png"}),
        validators=default_validators(),
    )
    uploaded = request.files["file"]
    try:
        result = Uploader(policy, storage).upload(
            as_uploadable(uploaded),
            bucket=current_app.config["UPLOADKIT_BUCKET"],
            object_name=uploaded.filename,
            after_upload=notify,  # or a Celery-like task with .delay
        )
    except UploaderError as exc:
        return json_error_response(exc)
    return jsonify({
        "object_name": result.object_name,
        "sha256": result.sha256,
        "etag": result.etag,
    })
```

## After-upload

Pass Core `after_upload` on `Uploader.upload`: a sync callback `(result) -> None`, or a Celery-like object with `.delay(**result.as_task_kwargs())`. The hook runs once after a successful put; exceptions propagate. Full semantics: [uploadkit Core README](https://github.com/uploadkit/uploadkit#after-upload-hooks).

## Architecture

Thin adapters over UploadKit Core. Werkzeug `FileStorage` does not duck-type `UploadableFile` (form field `name` vs upload `filename`), so `as_uploadable` maps the fields explicitly.

## Public API

| Symbol | Kind |
|--------|------|
| `as_uploadable` | Public |
| `json_error_response` / `status_for_error` / `error_payload` | Public |
| `get_storage_provider` | Public |

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
