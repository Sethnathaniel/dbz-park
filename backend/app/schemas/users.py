from pydantic import BaseModel, ConfigDict, Field

from app.schemas.tickets import TicketOut


class AccountOut(BaseModel):
    """An account as the staff sees it: who, how to reach them, and their tickets."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_staff: bool
    tickets: list[TicketOut]


class AccountUpdateIn(BaseModel):
    """What the staff can change on an account. The password stays the visitor's own."""

    username: str = Field(min_length=3, max_length=150)
    email: str = Field(max_length=254)
    is_staff: bool
