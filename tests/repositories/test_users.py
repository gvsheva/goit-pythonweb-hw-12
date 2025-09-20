import pytest

from app.auth import hash_password
from app.repositories.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    set_user_verified,
    update_avatar_url,
)


@pytest.mark.asyncio
async def test_create_and_get_user(session, mocker):
    commit_spy = mocker.spy(session, "commit")

    email = "user1@example.com"
    user = await create_user(session, email=email, hashed_password=hash_password("secret123"))
    assert user.id > 0
    assert user.email == email
    assert commit_spy.call_count == 1  # create_user commits

    by_email = await get_user_by_email(session, email)
    assert by_email is not None
    assert by_email.id == user.id

    by_id = await get_user_by_id(session, user.id)
    assert by_id is not None
    assert by_id.email == email


@pytest.mark.asyncio
async def test_set_user_verified_and_avatar(session, mocker):
    commit_spy = mocker.spy(session, "commit")

    user = await create_user(session, email="u2@example.com", hashed_password=hash_password("password123"))
    assert user.is_verified is False
    assert commit_spy.call_count == 1  # create_user commits

    user = await set_user_verified(session, user)
    assert user.is_verified is True
    assert commit_spy.call_count == 2  # set_user_verified commits

    user = await update_avatar_url(session, user, "https://cdn.example.com/avatar.png")
    assert user.avatar_url == "https://cdn.example.com/avatar.png"
    assert commit_spy.call_count == 3  # update_avatar_url commits
