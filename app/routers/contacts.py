from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.auth import get_current_user
from app.repositories.contacts import (
    create_contact,
    delete_contact,
    get_contact,
    list_contacts,
    upcoming_birthdays,
    update_contact,
)
from app.schemas import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact_endpoint(
    payload: ContactCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ContactRead:
    try:
        contact = await create_contact(
            session, user_id=current_user.id, **payload.model_dump()
        )
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this email already exists",
        )
    return ContactRead.model_validate(contact)


@router.get("", response_model=list[ContactRead])
async def list_contacts_endpoint(
    first_name: str | None = Query(None),
    last_name: str | None = Query(None),
    email: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    contacts = await list_contacts(
        session,
        user_id=current_user.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        limit=limit,
        offset=offset,
    )
    return [ContactRead.model_validate(c) for c in contacts]


@router.get("/upcoming_birthdays", response_model=list[ContactRead])
async def upcoming_birthdays_endpoint(
    days: int = Query(7, ge=1, le=31),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    contacts = await upcoming_birthdays(
        session, user_id=current_user.id, days=days, limit=limit, offset=offset
    )
    return [ContactRead.model_validate(c) for c in contacts]


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact_endpoint(
    contact_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    contact = await get_contact(session, current_user.id, contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return ContactRead.model_validate(contact)


@router.put("/{contact_id}", response_model=ContactRead)
async def update_contact_endpoint(
    contact_id: int,
    payload: ContactUpdate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    contact = await get_contact(session, current_user.id, contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )

    try:
        updated = await update_contact(
            session, contact, **payload.model_dump(exclude_unset=True)
        )
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this email already exists",
        )
    return ContactRead.model_validate(updated)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact_endpoint(
    contact_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> None:
    contact = await get_contact(session, current_user.id, contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    await delete_contact(session, contact)
    return None
