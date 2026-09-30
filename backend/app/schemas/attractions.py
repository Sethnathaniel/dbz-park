from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.tickets import TicketOut


class AttractionOut(BaseModel):
    """An attraction, and nothing about the visitor asking."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    # No column yet: the front shows its default illustration for "".
    photo_url: str = ""
    max_people: int
    people_inside: int
    avg_duration: int


class PositionOut(BaseModel):
    """Waiting places ahead, this one included: 1 = next in line, 0 = already called."""

    position: int


class MyEntryOut(BaseModel):
    """A place the caller holds, with where it stands."""

    id: int
    attraction_id: int
    ticket: TicketOut
    joined_at: datetime
    is_ready: bool
    ready_at: datetime | None
    max_seconds_allowing_ready: int
    ready_expired: bool
    position: int


class MyVisitOut(BaseModel):
    """An attraction the caller is inside right now."""

    model_config = ConfigDict(from_attributes=True)

    attraction_id: int
    ticket: TicketOut
    entered_at: datetime


class MyQueueOut(BaseModel):
    """Everything the caller has going on, which the catalogue deliberately leaves out."""

    entries: list[MyEntryOut]
    visits: list[MyVisitOut]
