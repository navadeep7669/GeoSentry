from __future__ import annotations
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status

from app.config import settings

_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is None:
        kwargs: dict = {
            "aws_access_key_id": settings.STORAGE_ACCESS_KEY,
            "aws_secret_access_key": settings.STORAGE_SECRET_KEY,
            "region_name": settings.STORAGE_REGION,
        }
        if settings.STORAGE_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.STORAGE_ENDPOINT_URL
        _s3_client = boto3.client("s3", **kwargs)
    return _s3_client


ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "video/mp4", "video/quicktime", "video/x-msvideo",
}
MAX_FILE_SIZE_MB = 50


async def upload_file(file: UploadFile, report_id: int) -> str:
    """Upload a file to S3/MinIO and return the public URL."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit",
        )

    ext = (file.filename or "file").rsplit(".", 1)[-1].lower()
    key = f"reports/{report_id}/{uuid.uuid4()}.{ext}"

    client = _get_client()
    try:
        client.put_object(
            Bucket=settings.STORAGE_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=file.content_type,
        )
    except ClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage upload failed: {exc}",
        )

    if settings.STORAGE_ENDPOINT_URL:
        # MinIO or custom endpoint
        return f"{settings.STORAGE_ENDPOINT_URL}/{settings.STORAGE_BUCKET_NAME}/{key}"
    else:
        return f"https://{settings.STORAGE_BUCKET_NAME}.s3.{settings.STORAGE_REGION}.amazonaws.com/{key}"
