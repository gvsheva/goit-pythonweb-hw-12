import pytest
from datetime import date, timedelta

from app.auth import hash_password
from app.repositories.users import create_user
from app.repositories.contacts import (
    create_contact,
    delete_contact,
    get_contact,
    list_contacts,
    upcoming_birthdays,
    update_contact,
)


@pytest.mark.asyncio
async def test_create_list_get_update_delete_contacts(session, mocker, fake):
    commit_spy = mocker.spy(session, "commit")

    # Create user
    user = await create_user(session, email=fake.unique.email(), hashed_password=hash_password(fake.password(length=12)))
    other = await create_user(session, email=fake.unique.email(), hashed_password=hash_password(fake.password(length=12)))
    assert commit_spy.call_count == 2  # two users created

    # Create contacts for both users
    c1 = await create_contact(
        session,
        user_id=user.id,
        first_name="John",
        last_name="Doe",
        email=fake.unique.email(),
        phone=fake.phone_number(),
        birthday=None,
        extra_info=None,
    )
    assert c1.id > 0
    assert commit_spy.call_count == 3

    # Same email for a different user is allowed (per-user unique)
    c_other = await create_contact(
        session,
        user_id=other.id,
        first_name="John",
        last_name="Smith",
        email=c1.email,
        phone=fake.phone_number(),
        birthday=None,
        extra_info=None,
    )
    assert c_other.id > 0
    assert c_other.user_id == other.id
    assert commit_spy.call_count == 4

    # List with filters
    all_user_contacts = await list_contacts(session, user_id=user.id)
    assert len(all_user_contacts) == 1

    filtered = await list_contacts(session, user_id=user.id, first_name="jo")
    assert len(filtered) == 1
    filtered_none = await list_contacts(session, user_id=user.id, last_name="smith")
    assert len(filtered_none) == 0

    # Get by id with ownership
    got = await get_contact(session, user_id=user.id, contact_id=c1.id)
    assert got is not None
    wrong_owner = await get_contact(session, user_id=other.id, contact_id=c1.id)
    assert wrong_owner is None

    # Update
    updated = await update_contact(session, c1, phone="99999", extra_info="Friend")
    assert updated.phone == "99999"
    assert updated.extra_info == "Friend"
    assert commit_spy.call_count == 5

    # Delete
    await delete_contact(session, updated)
    after_delete = await get_contact(session, user_id=user.id, contact_id=c1.id)
    assert after_delete is None
    assert commit_spy.call_count == 6


@pytest.mark.asyncio
async def test_upcoming_birthdays_postgres_only(session, fake):
    # Skip if not using PostgreSQL (function relies on PostgreSQL-specific SQL)
    engine = session.bind
    engine_url = getattr(engine, "url", None)
    if engine_url is None or "postgresql" not in str(engine_url):
        pytest.skip("upcoming_birthdays requires PostgreSQL")

    user = await create_user(session, email=fake.unique.email(), hashed_password=hash_password(fake.password(length=12)))

    today = date.today()
    in_3 = today + timedelta(days=3)
    in_10 = today + timedelta(days=10)
    yesterday = today - timedelta(days=1)

    # Helper to set birthday with the same month/day but fixed year
    def md(d: date) -> date:
        return date(2000, d.month, d.day)

    # Create contacts with various birthdays
    c_today = await create_contact(
        session,
        user_id=user.id,
        first_name="Today",
        last_name="Person",
        email="today@example.com",
        phone="1",
        birthday=md(today),
        extra_info=None,
    )
    c_in3 = await create_contact(
        session,
        user_id=user.id,
        first_name="Soon",
        last_name="Person",
        email="soon@example.com",
        phone="2",
        birthday=md(in_3),
        extra_info=None,
    )
    c_in10 = await create_contact(
        session,
        user_id=user.id,
        first_name="Later",
        last_name="Person",
        email="later@example.com",
        phone="3",
        birthday=md(in_10),
        extra_info=None,
    )
    c_yest = await create_contact(
        session,
        user_id=user.id,
        first_name="Past",
        last_name="Person",
        email="past@example.com",
        phone="4",
        birthday=md(yesterday),
        extra_info=None,
    )

    # Query upcoming birthdays (next 3 days)
    upcoming = await upcoming_birthdays(session, user_id=user.id, days=3)
    emails = {c.email for c in upcoming}

    assert "today@example.com" in emails
    assert "soon@example.com" in emails
    assert "past@example.com" not in emails
    assert "later@example.com" not in emails
