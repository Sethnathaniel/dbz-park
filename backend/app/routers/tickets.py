"""Tickets.

Two listings, with different rights: `GET /tickets/` shows every ticket with its holder
and is staff-only — the single response of the API that ties a ticket to a name — while
`GET /user/<id>/tickets/` shows one visitor's, readable by that visitor or by staff.
A ticket is usable as soon as it exists: there is no payment step.
"""

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select, text, update
from sqlalchemy.orm import selectinload

from app.db import SessionDep
from app.dependencies import CurrentUser, StaffUser
from app.errors import UNKNOWN_TICKET, UNKNOWN_USER, ApiError
from app.models import Ticket, User
from app.schemas.tickets import TicketAdminOut, TicketAssignIn, TicketCreateIn, TicketOut

router = APIRouter(prefix="/tickets", tags=["tickets"])

# One visitor's tickets live under the visitor: the address says whose they are.
user_router = APIRouter(prefix="/user", tags=["tickets"])


@router.get("/", response_model=list[TicketAdminOut])
async def list_all_tickets(staff: StaffUser, session: SessionDep) -> list[Ticket]:
    """Every ticket in the park, assigned or not, with its holder.

    Closed to visitors: everywhere else the API is built so nothing can be learnt about
    someone else's tickets, and this is the exception that must stay behind `is_staff`.
    """
    tickets = await session.scalars(
        select(Ticket).options(selectinload(Ticket.user)).order_by(Ticket.id)
    )
    return list(tickets)


@user_router.get("/{user_id}/tickets/", response_model=list[TicketOut])
async def list_user_tickets(user_id: int, user: CurrentUser, session: SessionDep) -> list[Ticket]:
    """One visitor's tickets: themself, or a staff account."""
    if user_id == user.id or user.is_staff:
        # Same answer as an account that does not exist, so the route cannot enumerate them.
        tickets = await session.scalars(
            select(Ticket).where(Ticket.user_id == user_id).order_by(Ticket.created_at, Ticket.id)
        )
        return list(tickets)
    raise ApiError(UNKNOWN_USER)


@router.post("/", response_model=TicketOut)
async def create_ticket(data: TicketCreateIn, user: CurrentUser, session: SessionDep) -> Ticket:
    """Buys a ticket: the row is created, attached to the caller, usable right away. """
    # Taking the id from the sequence first keeps `numero` unique without a second write.
    number = await session.scalar(text("SELECT nextval(pg_get_serial_sequence('ticket', 'id'))"))
    ticket = Ticket(
        id=number,
        user_id=user.id,
        numero=f"DBZ-{number:04d}",
        role=data.role.strip().lower(),
        created_at=datetime.now(),
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


@router.post("/assign/", response_model=TicketOut)
async def assign_ticket(data: TicketAssignIn, user: CurrentUser, session: SessionDep) -> Ticket:
    """Claims a ticket bought elsewhere, from its number alone."""
    # One statement: two visitors claiming the same number at once, only one wins.
    claimed = await session.scalar(
        update(Ticket)
        .where(Ticket.numero == data.numero, Ticket.user_id.is_(None))
        .values(user_id=user.id)
        .returning(Ticket)
    )
    if claimed is None:
        # Unknown number and already-taken number end here together, on purpose.
        raise ApiError(UNKNOWN_TICKET)

    await session.commit()
    await session.refresh(claimed)
    return claimed
