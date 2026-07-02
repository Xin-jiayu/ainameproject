"""cleanup legacy admin email

Revision ID: e2b6a4c9d8f1
Revises: d1a9c7e5f2b4
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2b6a4c9d8f1"
down_revision: Union[str, None] = "d1a9c7e5f2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEGACY_EMAIL = "admin@ainame.local"
CLEAN_EMAIL = "legacy-admin-disabled@example.com"


def upgrade() -> None:
    bind = op.get_bind()
    legacy_user = bind.execute(
        sa.text('select id from `user` where email = :email'),
        {"email": LEGACY_EMAIL},
    ).first()
    if not legacy_user:
        return

    clean_user = bind.execute(
        sa.text('select id from `user` where email = :email'),
        {"email": CLEAN_EMAIL},
    ).first()
    next_email = CLEAN_EMAIL if not clean_user else f"legacy-admin-disabled-{legacy_user.id}@example.com"

    bind.execute(
        sa.text(
            'update `user` set email = :email, username = :username, '
            'is_admin = 0, is_frozen = 1 where id = :id'
        ),
        {"email": next_email, "username": "legacy_admin_disabled", "id": legacy_user.id},
    )


def downgrade() -> None:
    pass
