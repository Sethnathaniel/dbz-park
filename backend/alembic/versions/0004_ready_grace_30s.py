"""A called visitor now has 30 seconds to show up, down from 300.

Only new places get it: a place already in the queue keeps the delay it was promised.

Revision ID: 0004_ready_grace_30s
Revises: 0003_role_without_default
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_ready_grace_30s"
down_revision: str | None = "0003_role_without_default"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("queue_entry", "max_seconds_allowing_ready", server_default=sa.text("30"))


def downgrade() -> None:
    op.alter_column("queue_entry", "max_seconds_allowing_ready", server_default=sa.text("300"))
