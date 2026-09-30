"""The virtual queue: one row per ticket waiting on an attraction.

The table holds the present moment only — a place disappears when its holder goes in or
walks away, hence at most one ticket per attraction.
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, false, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.attraction import Attraction
    from app.models.ticket import Ticket


class QueueEntry(Base):
    __tablename__ = "queue_entry"
    __table_args__ = (
        UniqueConstraint(
            "attraction_id", "ticket_id", name="uq_queue_entry_ticket_per_attraction"
        ),
        {"comment": "Virtual queue: one row per ticket waiting on an attraction."},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    attraction_id: Mapped[int] = mapped_column(
        ForeignKey("attraction.id", ondelete="CASCADE"), index=True
    )
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.id", ondelete="CASCADE"), index=True)

    # Arrival order: this date is what gives the rank in the queue.
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    is_ready: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    ready_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Grace period in seconds: past it, the turn was missed and the place goes to another.
    max_seconds_allowing_ready: Mapped[int] = mapped_column(
        Integer,
        default=30,
        server_default=text("30"),
        comment="grace period in seconds before the ready state expires",
    )

    attraction: Mapped["Attraction"] = relationship(back_populates="queue_entries")
    ticket: Mapped["Ticket"] = relationship(back_populates="queue_entries")

    def ready_expired(self, now: datetime | None = None) -> bool:
        """Has the grace period elapsed? Computed here, never by the front."""
        if not self.is_ready or self.ready_at is None:
            return False
        now = now or datetime.now()
        return now - self.ready_at > timedelta(seconds=self.max_seconds_allowing_ready)

    def __repr__(self) -> str:
        return f"<QueueEntry #{self.id} attraction={self.attraction_id} ticket={self.ticket_id}>"
