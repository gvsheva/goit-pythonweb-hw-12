"""Repository functions for User entity."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Get a user by email.

    Args:
        session: Async SQLAlchemy session.
        email: Email address to search for.

    Returns:
        User if found, otherwise None.
    """
    res = await session.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Get a user by primary ID.

    Args:
        session: Async SQLAlchemy session.
        user_id: User primary key.

    Returns:
        User if found, otherwise None.
    """
    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def create_user(
    session: AsyncSession, *, email: str, hashed_password: str
) -> User:
    """Create and persist a new user.

    Args:
        session: Async SQLAlchemy session.
        email: User email (must be unique).
        hashed_password: Bcrypt hashed password.

    Returns:
        Newly created User.
    """
    user = User(email=email, hashed_password=hashed_password, is_verified=False)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def set_user_verified(session: AsyncSession, user: User) -> User:
    """Mark user's email as verified.

    Args:
        session: Async SQLAlchemy session.
        user: User to update.

    Returns:
        Updated User instance.
    """
    user.is_verified = True
    await session.commit()
    await session.refresh(user)
    return user


async def update_avatar_url(
    session: AsyncSession, user: User, avatar_url: str | None
) -> User:
    """Update and persist user's avatar URL.

    Args:
        session: Async SQLAlchemy session.
        user: User to update.
        avatar_url: New avatar URL or None to clear.

    Returns:
        Updated User instance.
    """
    user.avatar_url = avatar_url
    await session.commit()
    await session.refresh(user)
    return user
