"""The role column stops inventing a value: every insert states one.

Revision ID: 0003_role_without_default
Revises: 0002_role_as_text
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_role_without_default"
down_revision: str | None = "0002_role_as_text"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("ticket", "role", server_default=None)


def downgrade() -> None:
    op.alter_column("ticket", "role", server_default=sa.text("'normal'"))
