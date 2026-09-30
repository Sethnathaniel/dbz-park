from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketOut(BaseModel):
    """A ticket as shown to its holder — no holder inside, they know it is theirs."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    role: str
    created_at: datetime


class TicketHolderOut(BaseModel):
    """Just enough to name the holder in the staff listing."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class TicketAdminOut(TicketOut):
    """Staff-only shape: the ticket and who holds it.

    The one response of the API that ties a ticket to a name, hence `GET /tickets/`
    being closed to visitors.
    """

    user: TicketHolderOut | None = None


class TicketCreateIn(BaseModel):
    """The role is taken as it comes: the back lowercases it and stores it."""

    role: str = Field(min_length=1, max_length=32)


class TicketAssignIn(BaseModel):
    numero: str = Field(min_length=1, max_length=32)
