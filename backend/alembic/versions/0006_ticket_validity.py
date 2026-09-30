"""A ticket can be invalidated by hand by the staff. Existing tickets stay valid.

Revision ID: 0006_ticket_validity
Revises: 0005_attraction_incident
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_ticket_validity"
down_revision: str | None = "0005_attraction_incident"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ticket",
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("ticket", "is_valid")
