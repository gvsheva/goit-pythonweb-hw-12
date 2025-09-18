from datetime import date

from sqlalchemy import Date, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("email", name="uq_contacts_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    extra_info: Mapped[str | None] = mapped_column(Text, nullable=True)
