"""Create contacts table

Revision ID: 0001_create_contacts
Revises: 
Create Date: 2025-09-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_create_contacts"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("birthday", sa.Date(), nullable=True),
        sa.Column("extra_info", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_contacts_email", "contacts", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_contacts_email", "contacts", type_="unique")
    op.drop_table("contacts")
