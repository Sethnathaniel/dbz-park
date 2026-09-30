"""An attraction can be out of service: its queue pauses until the admin reopens it.

Revision ID: 0005_attraction_incident
Revises: 0004_ready_grace_30s
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_attraction_incident"
down_revision: str | None = "0004_ready_grace_30s"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "attraction",
        sa.Column(
            "incident_reason",
            sa.String(200),
            nullable=True,
            comment="why the attraction is out of service, null when open",
        ),
    )
    op.add_column("attraction", sa.Column("incident_since", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("attraction", "incident_since")
    op.drop_column("attraction", "incident_reason")
