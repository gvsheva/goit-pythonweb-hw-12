"""Add role column to users (user/admin)

Revision ID: 0003_user_roles
Revises: 0002_users_and_contact_owner
Create Date: 2025-09-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_user_roles"
down_revision: Union[str, Sequence[str], None] = "0002_users_and_contact_owner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
    )
    # Опціонально: прибрати server_default після заповнення існуючих рядків
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "role")
