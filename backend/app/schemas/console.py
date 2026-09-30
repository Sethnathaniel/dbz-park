from datetime import datetime

from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.schemas.tickets import TicketOut


class ConsoleAttractionOut(BaseModel):
    id: int
    name: str
    max_people: int
    incident_reason: str | None
    incident_since: datetime | None


class IncidentIn(BaseModel):
    """What the admin types when stopping an attraction: visitors read it as is."""

    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ConsoleReadyOut(BaseModel):
    """A visitor who has been called, waiting on the admin's decision."""

    id: int
    username: str
    ticket: TicketOut
    ready_at: datetime | None
    max_seconds_allowing_ready: int
    ready_expired: bool


class ConsoleRowOut(BaseModel):
    """One row per attraction, including those where nobody is called (`ready: []`)."""

    attraction: ConsoleAttractionOut
    inside: int
    waiting: int
    ready: list[ConsoleReadyOut]
