"""Add users table and contact ownership

Revision ID: 0002_users_and_contact_owner
Revises: 0001_create_contacts
Create Date: 2025-09-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_users_and_contact_owner"
down_revision: Union[str, Sequence[str], None] = "0001_create_contacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "email", sa.String(length=255), nullable=False, unique=True, index=True
        ),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "is_verified", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")
        ),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.add_column("contacts", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_contacts_user",
        "contacts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("uq_contacts_email", "contacts", type_="unique")
    op.create_unique_constraint(
        "uq_contacts_user_email", "contacts", ["user_id", "email"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_contacts_user_email", "contacts", type_="unique")
    op.create_unique_constraint("uq_contacts_email", "contacts", ["email"])

    op.drop_constraint("fk_contacts_user", "contacts", type_="foreignkey")
    op.drop_column("contacts", "user_id")

    op.drop_table("users")
