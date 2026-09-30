"""Account management, staff only: find, edit or delete an account, and switch a ticket
off or back on by hand.

Two guards keep an admin from locking themself out of the console: they can neither
delete their own account nor drop their own staff rights.
"""

from fastapi import APIRouter, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import SessionDep
from app.dependencies import StaffUser
from app.errors import UNKNOWN_ACCOUNT, UNKNOWN_TICKET, USERNAME_TAKEN, ApiError
from app.models import QueueEntry, Ticket, User
from app.schemas.tickets import TicketOut
from app.schemas.users import AccountOut, AccountUpdateIn

router = APIRouter(prefix="/console", tags=["accounts"])

# Enough to find someone by name; past that, the search should be more precise.
SEARCH_LIMIT = 50


async def any_account(session: AsyncSession, user_id: int) -> User:
    account = await session.scalar(
        select(User).where(User.id == user_id).options(selectinload(User.tickets))
    )
    if account is None:
        raise ApiError(UNKNOWN_ACCOUNT)
    return account


async def any_ticket(session: AsyncSession, ticket_id: int) -> Ticket:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        raise ApiError(UNKNOWN_TICKET)
    return ticket


async def leave_every_queue(session: AsyncSession, ticket_ids: list[int]) -> None:
    """Removes these tickets from every queue. Visits are left alone: people inside stay."""
    await session.execute(delete(QueueEntry).where(QueueEntry.ticket_id.in_(ticket_ids)))


@router.get("/users/", response_model=list[AccountOut])
async def search_accounts(staff: StaffUser, session: SessionDep, search: str = "") -> list[User]:
    """Accounts whose name or e-mail contains `search`, alphabetically. Empty: the first ones."""
    query = (
        select(User).options(selectinload(User.tickets)).order_by(User.username).limit(SEARCH_LIMIT)
    )
    if search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(User.username.ilike(pattern) | User.email.ilike(pattern))
    return list(await session.scalars(query))


@router.post("/users/{user_id}/", response_model=AccountOut)
async def update_account(
    user_id: int, data: AccountUpdateIn, staff: StaffUser, session: SessionDep
) -> User:
    """Renames an account, changes its e-mail, or gives or takes staff rights."""
    account = await any_account(session, user_id)
    if account.id == staff.id and not data.is_staff:
        raise ApiError("Vous ne pouvez pas retirer vos propres droits d'admin.")

    taken = await session.scalar(
        select(User.id).where(User.username == data.username, User.id != account.id)
    )
    if taken is not None:
        raise ApiError(USERNAME_TAKEN)

    account.username = data.username
    account.email = data.email
    account.is_staff = data.is_staff
    await session.commit()
    return account


@router.post("/users/{user_id}/delete/")
async def delete_account(user_id: int, staff: StaffUser, session: SessionDep) -> Response:
    """Deletes an account. Its places in the queues go with it; its tickets stay in the
    park, unassigned, so whoever holds the number can claim them again.
    """
    account = await any_account(session, user_id)
    if account.id == staff.id:
        raise ApiError("Vous ne pouvez pas supprimer votre propre compte.")

    await leave_every_queue(session, [ticket.id for ticket in account.tickets])
    await session.delete(account)
    await session.commit()
    return Response(status_code=200)


@router.post("/tickets/{ticket_id}/revoke/", response_model=TicketOut)
async def revoke_ticket(ticket_id: int, staff: StaffUser, session: SessionDep) -> Ticket:
    """Switches a ticket off: it leaves every queue and can no longer join one."""
    ticket = await any_ticket(session, ticket_id)
    ticket.is_valid = False
    await leave_every_queue(session, [ticket.id])
    await session.commit()
    return ticket


@router.post("/tickets/{ticket_id}/restore/", response_model=TicketOut)
async def restore_ticket(ticket_id: int, staff: StaffUser, session: SessionDep) -> Ticket:
    """Switches a ticket back on. The places it lost are not given back."""
    ticket = await any_ticket(session, ticket_id)
    ticket.is_valid = True
    await session.commit()
    return ticket
