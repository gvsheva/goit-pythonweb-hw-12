"""Repository functions for Contact entity."""
from datetime import date

from sqlalchemy import Select, and_, select, func, cast, Date, Integer, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact


async def list_contacts(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """List user's contacts with optional filters and pagination.

    Args:
        session: Async SQLAlchemy session.
        user_id: Owner user ID.
        first_name: Optional case-insensitive filter by first name (substring).
        last_name: Optional case-insensitive filter by last name (substring).
        email: Optional case-insensitive filter by email (substring).
        limit: Max number of records to return.
        offset: Number of records to skip (for pagination).

    Returns:
        List of Contact objects.
    """
    stmt: Select = select(Contact).where(Contact.user_id == user_id)
    filters = []

    if first_name:
        filters.append(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        filters.append(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        filters.append(Contact.email.ilike(f"%{email}%"))

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.limit(limit).offset(offset)

    res = await session.execute(stmt)
    return res.scalars().all()


async def get_contact(session: AsyncSession, user_id: int, contact_id: int):
    """Fetch a single contact by ID owned by the given user.

    Args:
        session: Async SQLAlchemy session.
        user_id: Owner user ID.
        contact_id: Contact primary ID.

    Returns:
        Contact if found, otherwise None.
    """
    res = await session.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id)
    )
    return res.scalar_one_or_none()


async def create_contact(
    session: AsyncSession,
    *,
    user_id: int,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    birthday: date | None = None,
    extra_info: str | None = None,
):
    """Create and persist a new contact.

    Args:
        session: Async SQLAlchemy session.
        user_id: Owner user ID.
        first_name: Contact first name.
        last_name: Contact last name.
        email: Contact email.
        phone: Contact phone number.
        birthday: Optional date of birth.
        extra_info: Optional extra information.

    Returns:
        Newly created Contact.
    """
    contact = Contact(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        birthday=birthday,
        extra_info=extra_info,
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def update_contact(
    session: AsyncSession,
    contact: Contact,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    birthday: date | None = None,
    extra_info: str | None = None,
):
    """Update fields of an existing contact and commit the changes.

    Args:
        session: Async SQLAlchemy session.
        contact: Contact instance to update.
        first_name: Optional new first name.
        last_name: Optional new last name.
        email: Optional new email.
        phone: Optional new phone number.
        birthday: Optional new birthday.
        extra_info: Optional new extra info.

    Returns:
        Updated Contact instance.
    """
    if first_name is not None:
        contact.first_name = first_name
    if last_name is not None:
        contact.last_name = last_name
    if email is not None:
        contact.email = email
    if phone is not None:
        contact.phone = phone
    if birthday is not None:
        contact.birthday = birthday
    if extra_info is not None:
        contact.extra_info = extra_info

    await session.commit()
    await session.refresh(contact)
    return contact


async def delete_contact(session: AsyncSession, contact: Contact) -> None:
    """Delete the given contact.

    Args:
        session: Async SQLAlchemy session.
        contact: Contact to remove.

    Returns:
        None
    """
    await session.delete(contact)
    await session.commit()


async def upcoming_birthdays(
    session: AsyncSession,
    user_id: int,
    days: int = 7,
    limit: int = 100,
    offset: int = 0,
):
    """Return contacts with birthdays within the next N days using SQL-side filtering.

    Args:
        session: Async SQLAlchemy session.
        user_id: Owner user ID.
        days: Window size in days to check ahead.
        limit: Max number of records to return.
        offset: Number of records to skip.

    Returns:
        List of Contact objects with birthdays within the window.
    """
    today = func.current_date()
    # SQLAlchemy func doesn't support keyword args for PostgreSQL make_interval; use positional:
    # make_interval(years, months, weeks, days, hours, mins, secs)
    window_end = cast(func.current_date() + func.make_interval(0, 0, 0, days, 0, 0, 0), Date)

    # Build the next upcoming birthday date for the current year,
    # adding 1 year when the month-day has already passed today.
    bday_mmdd_lt_today = func.to_char(Contact.birthday, "MM-DD") < func.to_char(today, "MM-DD")
    next_year = cast(func.date_part("year", today), Integer) + case(
        (bday_mmdd_lt_today, 1), else_=0
    )
    next_birthday_date = func.make_date(
        next_year,
        cast(func.date_part("month", Contact.birthday), Integer),
        cast(func.date_part("day", Contact.birthday), Integer),
    )

    stmt: Select = (
        select(Contact)
        .where(
            Contact.user_id == user_id,
            Contact.birthday.is_not(None),
            next_birthday_date >= today,
            next_birthday_date <= window_end,
        )
        .order_by(next_birthday_date)
        .limit(limit)
        .offset(offset)
    )

    res = await session.execute(stmt)
    return res.scalars().all()
