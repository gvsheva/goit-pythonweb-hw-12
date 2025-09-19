from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    res = await session.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def create_user(
    session: AsyncSession, *, email: str, hashed_password: str
) -> User:
    user = User(email=email, hashed_password=hashed_password, is_verified=False)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def set_user_verified(session: AsyncSession, user: User) -> User:
    user.is_verified = True
    await session.commit()
    await session.refresh(user)
    return user


async def update_avatar_url(
    session: AsyncSession, user: User, avatar_url: str | None
) -> User:
    user.avatar_url = avatar_url
    await session.commit()
    await session.refresh(user)
    return user
