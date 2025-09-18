from __future__ import annotations

from datetime import date

from sqlalchemy import Select, and_, select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact


async def list_contacts(
    session: AsyncSession,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    stmt: Select = select(Contact)
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


async def get_contact(session: AsyncSession, contact_id: int):
    res = await session.execute(select(Contact).where(Contact.id == contact_id))
    return res.scalar_one_or_none()


async def create_contact(
    session: AsyncSession,
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    birthday: date | None = None,
    extra_info: str | None = None,
):
    contact = Contact(
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
    await session.delete(contact)
    await session.commit()


async def upcoming_birthdays(
    session: AsyncSession,
    days: int = 7,
    limit: int = 100,
    offset: int = 0,
):
    today = func.current_date()
    end_date = cast(func.current_date() + func.make_interval(days=days), Date)

    bday_mmdd = func.to_char(Contact.birthday, "MM-DD")
    start_mmdd = func.to_char(today, "MM-DD")
    end_mmdd = func.to_char(end_date, "MM-DD")

    same_year = func.to_char(end_date, "YYYY") == func.to_char(today, "YYYY")
    cond_same = (bday_mmdd >= start_mmdd) & (bday_mmdd <= end_mmdd)
    cond_wrap = (bday_mmdd >= start_mmdd) | (bday_mmdd <= end_mmdd)

    stmt: Select = (
        select(Contact)
        .where(
            Contact.birthday.is_not(None),
                (same_year & cond_same) | (~same_year & cond_wrap),
        )
        .limit(limit)
        .offset(offset)
    )

    res = await session.execute(stmt)
    return res.scalars().all()
