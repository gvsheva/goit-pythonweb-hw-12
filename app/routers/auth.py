from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db import get_session
from app.repositories.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    set_user_verified,
)
from app.schemas import RefreshRequest, Token, UserCreate, UserRead
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

def get_fastmail_config() -> ConnectionConfig:
    use_credentials = (
        settings.mail_use_credentials
        if settings.mail_use_credentials is not None
        else bool(settings.mail_username)
    )
    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username or "",
        MAIL_PASSWORD=settings.mail_password or "",
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=use_credentials,
        VALIDATE_CERTS=False,
    )


async def send_verification_email(email: str, token: str) -> None:
    base = settings.public_base_url.rstrip("/")
    verification_link = f"{base}/auth/verify?token={token}"
    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"Please verify your email by clicking the link: {verification_link}",
        subtype=MessageType.plain,
    )
    fm = FastMail(get_fastmail_config())
    await fm.send_message(message)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    existing = await get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    user = await create_user(
        session, email=payload.email, hashed_password=hash_password(payload.password)
    )
    # Send verification email
    verify_token = create_access_token(
        {"sub": str(user.id), "email": user.email, "scope": "verify"}
    )
    background_tasks.add_task(send_verification_email, user.email, verify_token)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_email(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    access_token = create_access_token(
        {"sub": str(user.id), "email": user.email, "scope": "access"}
    )
    refresh_token = create_refresh_token(
        {"sub": str(user.id), "email": user.email, "scope": "refresh"}
    )
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh(
    payload: RefreshRequest, session: AsyncSession = Depends(get_session)
):
    from app.auth import decode_token

    data = decode_token(payload.refresh_token)
    if data.get("scope") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    try:
        user_id = int(data.get("sub", 0))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    access_token = create_access_token(
        {"sub": str(user.id), "email": user.email, "scope": "access"}
    )
    refresh_token = create_refresh_token(
        {"sub": str(user.id), "email": user.email, "scope": "refresh"}
    )
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/request-verification")
async def request_verification_token(
    background_tasks: BackgroundTasks,
    email: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "scope": "verify"}
    )
    background_tasks.add_task(send_verification_email, user.email, token)
    return {"detail": "Verification email sent"}


@router.get("/verify")
async def verify_email(
    token: str = Query(...), session: AsyncSession = Depends(get_session)
):
    from app.auth import decode_token

    payload = decode_token(token)
    if payload.get("scope") != "verify":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token"
        )
    user_id = int(payload.get("sub", 0))
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.is_verified:
        return {"detail": "Email already verified"}
    await set_user_verified(session, user)
    return {"detail": "Email verified successfully"}
