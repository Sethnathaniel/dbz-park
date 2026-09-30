"""A ticket: a unique `numero`, a `role` fixed at purchase, and a holder that stays
`null` until somebody claims it. No payment state — a ticket is usable as soon as it
exists, which is why no column here mentions money.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.attraction_visit import AttractionVisit
    from app.models.queue_entry import QueueEntry
    from app.models.user import User


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    numero: Mapped[str] = mapped_column(String(32), unique=True)

    # Free text, lowercased on the way in, and always given: the column invents nothing.
    role: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User | None"] = relationship(back_populates="tickets")
    queue_entries: Mapped[list["QueueEntry"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
    visits: Mapped[list["AttractionVisit"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ticket {self.numero} ({self.role})>"
