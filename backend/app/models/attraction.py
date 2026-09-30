"""An attraction of the park."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.attraction_visit import AttractionVisit
    from app.models.queue_entry import QueueEntry


class Attraction(Base):
    __tablename__ = "attraction"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    max_people: Mapped[int] = mapped_column(Integer)

    # An integer rather than an interval: the front reads it as is.
    avg_duration: Mapped[int] = mapped_column(
        Integer, default=120, server_default=text("120"), comment="one ride, in seconds"
    )

    # A counter, not a count: whoever writes an entry or an exit must move it too.
    people_inside: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        comment="counter kept in step with attraction_visit, not a count",
    )

    # An incident pauses the queue: nobody is called, nobody gets in, and everyone keeps
    # their place. The reason being set is what says there is one.
    incident_reason: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="why the attraction is out of service, null when open"
    )
    incident_since: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    queue_entries: Mapped[list["QueueEntry"]] = relationship(
        back_populates="attraction", cascade="all, delete-orphan"
    )
    visits: Mapped[list["AttractionVisit"]] = relationship(
        back_populates="attraction", cascade="all, delete-orphan"
    )

    @property
    def is_full(self) -> bool:
        return self.people_inside >= self.max_people

    @property
    def out_of_service(self) -> bool:
        return self.incident_reason is not None

    def __repr__(self) -> str:
        return f"<Attraction {self.name}>"
