"""Ticket role becomes free text: the park can invent a fare without a migration.

Revision ID: 0002_role_as_text
Revises: 0001_initial
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_role_as_text"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ticket_role = postgresql.ENUM(
    "super_sayan", "sayan", "normal", name="ticket_role", create_type=False
)


def upgrade() -> None:
    # The default is typed by the enum, so it has to go before the column can change type.
    op.alter_column("ticket", "role", server_default=None)
    op.alter_column(
        "ticket",
        "role",
        type_=sa.String(length=32),
        existing_nullable=False,
        postgresql_using="role::text",
    )
    op.alter_column("ticket", "role", server_default=sa.text("'normal'"))
    op.execute("DROP TYPE ticket_role")


def downgrade() -> None:
    # Any fare invented since would not fit back into the enum, and the cast would fail.
    ticket_role.create(op.get_bind(), checkfirst=True)
    op.alter_column("ticket", "role", server_default=None)
    op.alter_column(
        "ticket",
        "role",
        type_=ticket_role,
        existing_nullable=False,
        postgresql_using="role::ticket_role",
    )
    op.alter_column("ticket", "role", server_default=sa.text("'normal'"))
