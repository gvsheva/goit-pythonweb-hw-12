"""User profile endpoints."""
import time

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.limiter import limiter

from app.auth import get_current_user
from app.config import settings
from app.db import get_session
from app.repositories.users import update_avatar_url
from app.schemas import UserRead

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserRead)
@limiter.limit("5/minute")
async def get_me(request: Request, current_user=Depends(get_current_user)):
    return UserRead.model_validate(current_user)


@router.put("/me/avatar", response_model=UserRead)
async def update_avatar(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    cloud_url = settings.cloudinary_url
    if not cloud_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary is not configured",
        )
    cloudinary.config(cloudinary_url=cloud_url)
    try:
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="avatars",
            public_id=f"user_{current_user.id}",
            overwrite=True,
            resource_type="image",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Avatar upload failed"
        ) from e

    avatar_url = upload_result.get("secure_url")
    user = await update_avatar_url(session, current_user, avatar_url)
    return UserRead.model_validate(user)
