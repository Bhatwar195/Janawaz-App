"""
Cloudinary integration for photo uploads.
When CLOUDINARY_CLOUD_NAME is set, uploads go to Cloudinary.
When it is not set (local dev), files are saved to the local uploads/ folder.
"""
import os
import uuid
from typing import Optional

CLOUDINARY_ENABLED = bool(os.getenv("CLOUDINARY_CLOUD_NAME"))

if CLOUDINARY_ENABLED:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

# Local uploads folder (used when Cloudinary is not configured)
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


async def upload_image(file) -> Optional[str]:
    """
    Upload an image from a FastAPI UploadFile.

    Returns:
        - A Cloudinary HTTPS URL if Cloudinary is configured.
        - A local filename string (e.g. 'abc123.jpg') if running locally.
        - None if no file was provided or the file type is not allowed.
    """
    if not file or not file.filename:
        return None

    if not allowed(file.filename):
        return None

    content = await file.read()

    if CLOUDINARY_ENABLED:
        # Upload bytes directly to Cloudinary
        result = cloudinary.uploader.upload(
            content,
            folder="janawaz",
            resource_type="image",
            transformation=[
                {"width": 1200, "height": 900, "crop": "limit", "quality": "auto"},
            ],
        )
        return result.get("secure_url")  # Full HTTPS URL
    else:
        # Save locally
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            f.write(content)
        return filename  # Just the filename; router builds /uploads/filename URL
