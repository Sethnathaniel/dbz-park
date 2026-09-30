"""Places held in a queue: position, withdrawal, validation."""

from fastapi import APIRouter, Response
from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.admission import admit
from app.db import SessionDep
from app.dependencies import CurrentUser
from app.errors import NOT_CALLED, TURN_MISSED, UNKNOWN_ENTRY, ApiError
from app.models import QueueEntry, Ticket, User
from app.schemas.attractions import PositionOut

router = APIRouter(prefix="/queue", tags=["queue"])


async def own_entry(session: AsyncSession, entry_id: int, user: User) -> QueueEntry:
    """The place, if it is this visitor's. Someone else's answers like one that does not exist."""
    entry = await session.scalar(
        select(QueueEntry).join(Ticket).where(QueueEntry.id == entry_id, Ticket.user_id == user.id)
    )
    if entry is None:
        raise ApiError(UNKNOWN_ENTRY)
    return entry


@router.get("/{entry_id}/position/", response_model=PositionOut)
async def queue_position(entry_id: int, user: CurrentUser, session: SessionDep) -> PositionOut:
    """First come, first served: the waiting places that joined before this one, plus itself."""
    entry = await own_entry(session, entry_id, user)
    if entry.is_ready:
        return PositionOut(position=0)

    position = await session.scalar(
        select(func.count())
        .select_from(QueueEntry)
        .where(
            QueueEntry.attraction_id == entry.attraction_id,
            QueueEntry.is_ready.is_(False),
            # The id breaks ties between two visitors who joined in the same instant.
            tuple_(QueueEntry.joined_at, QueueEntry.id) <= tuple_(entry.joined_at, entry.id),
        )
    )
    return PositionOut(position=position)


@router.post("/{entry_id}/leave/")
async def leave_queue(entry_id: int, user: CurrentUser, session: SessionDep) -> Response:
    """Voluntary withdrawal: the place disappears and the queue moves up."""
    await session.delete(await own_entry(session, entry_id, user))
    await session.commit()
    return Response(status_code=200)


@router.post("/{entry_id}/validate/")
async def validate_queue_entry(entry_id: int, user: CurrentUser, session: SessionDep) -> Response:
    """The visitor shows up after being called: the place becomes a visit, in one transaction."""
    entry = await own_entry(session, entry_id, user)
    if not entry.is_ready:
        raise ApiError(NOT_CALLED)
    if entry.ready_expired():
        raise ApiError(TURN_MISSED)

    await admit(session, entry)
    await session.commit()
    return Response(status_code=200)
