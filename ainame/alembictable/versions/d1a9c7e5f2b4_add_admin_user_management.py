"""add admin user management

Revision ID: d1a9c7e5f2b4
Revises: c4f8a2d1e9b0
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import os
import sqlalchemy as sa
from pwdlib import PasswordHash


# revision identifiers, used by Alembic.
revision: str = "d1a9c7e5f2b4"
down_revision: Union[str, None] = "c4f8a2d1e9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL") or os.getenv("MAIL_USERNAME") or "admin@ainame.local"
LEGACY_ADMIN_EMAIL = "admin@ainame.local"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin123456"


def upgrade() -> None:
    op.add_column("user", sa.Column("is_admin", sa.Boolean(), server_default="0", nullable=False))
    op.add_column("user", sa.Column("is_frozen", sa.Boolean(), server_default="0", nullable=False))

    bind = op.get_bind()
    exists = bind.execute(sa.text('select id from `user` where email = :email'), {"email": ADMIN_EMAIL}).first()
    if exists:
        bind.execute(
            sa.text('update `user` set is_admin = 1, is_frozen = 0 where email = :email'),
            {"email": ADMIN_EMAIL},
        )
        return

    legacy_admin = bind.execute(
        sa.text('select id from `user` where email = :email'),
        {"email": LEGACY_ADMIN_EMAIL},
    ).first()
    if legacy_admin:
        bind.execute(
            sa.text(
                'update `user` set email = :email, username = :username, '
                'is_admin = 1, is_frozen = 0 where email = :legacy_email'
            ),
            {"email": ADMIN_EMAIL, "username": ADMIN_USERNAME, "legacy_email": LEGACY_ADMIN_EMAIL},
        )
        return

    password_hash = PasswordHash.recommended().hash(ADMIN_PASSWORD)
    bind.execute(
        sa.text(
            'insert into `user` (email, username, free_quota, is_admin, is_frozen, _password) '
            'values (:email, :username, :free_quota, :is_admin, :is_frozen, :password)'
        ),
        {
            "email": ADMIN_EMAIL,
            "username": ADMIN_USERNAME,
            "free_quota": 999999,
            "is_admin": 1,
            "is_frozen": 0,
            "password": password_hash,
        },
    )


def downgrade() -> None:
    op.drop_column("user", "is_frozen")
    op.drop_column("user", "is_admin")
