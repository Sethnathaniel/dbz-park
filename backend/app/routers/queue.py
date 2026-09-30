"""Places held in a queue: position, withdrawal, validation."""

from fastapi import APIRouter, Response
from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admission import admit
from app.db import SessionDep
from app.dependencies import CurrentUser
from app.errors import NOT_CALLED, TURN_MISSED, UNKNOWN_ENTRY, ApiError
from app.models import AttractionVisit, QueueEntry, Ticket, User
from app.schemas.attractions import MyEntryOut, MyQueueOut, MyVisitOut, PositionOut
from app.schemas.tickets import TicketOut

router = APIRouter(prefix="/queue", tags=["queue"])


async def own_entry(session: AsyncSession, entry_id: int, user: User) -> QueueEntry:
    """The place, if it is this visitor's. Someone else's answers like one that does not exist."""
    entry = await session.scalar(
        select(QueueEntry).join(Ticket).where(QueueEntry.id == entry_id, Ticket.user_id == user.id)
    )
    if entry is None:
        raise ApiError(UNKNOWN_ENTRY)
    return entry


async def position_of(session: AsyncSession, entry: QueueEntry) -> int:
    """First come, first served: waiting places that joined before this one, plus itself."""
    if entry.is_ready:
        return 0
    return await session.scalar(
        select(func.count())
        .select_from(QueueEntry)
        .where(
            QueueEntry.attraction_id == entry.attraction_id,
            QueueEntry.is_ready.is_(False),
            # The id breaks ties between two visitors who joined in the same instant.
            tuple_(QueueEntry.joined_at, QueueEntry.id) <= tuple_(entry.joined_at, entry.id),
        )
    )


@router.get("/", response_model=MyQueueOut)
async def my_queue(user: CurrentUser, session: SessionDep) -> MyQueueOut:
    """The caller's places and visits: what the attraction cards need, the caller's only."""
    entries = await session.scalars(
        select(QueueEntry)
        .join(Ticket)
        .where(Ticket.user_id == user.id)
        .options(selectinload(QueueEntry.ticket))
        .order_by(QueueEntry.id)
    )
    visits = await session.scalars(
        select(AttractionVisit)
        .join(Ticket)
        .where(Ticket.user_id == user.id)
        .options(selectinload(AttractionVisit.ticket))
        .order_by(AttractionVisit.id)
    )
    return MyQueueOut(
        entries=[
            MyEntryOut(
                id=entry.id,
                attraction_id=entry.attraction_id,
                ticket=TicketOut.model_validate(entry.ticket),
                joined_at=entry.joined_at,
                is_ready=entry.is_ready,
                ready_at=entry.ready_at,
                max_seconds_allowing_ready=entry.max_seconds_allowing_ready,
                ready_expired=entry.ready_expired(),
                position=await position_of(session, entry),
            )
            for entry in entries
        ],
        visits=[MyVisitOut.model_validate(visit) for visit in visits],
    )


@router.get("/{entry_id}/position/", response_model=PositionOut)
async def queue_position(entry_id: int, user: CurrentUser, session: SessionDep) -> PositionOut:
    """Where this place stands: 1 = next in line, 0 = already called."""
    entry = await own_entry(session, entry_id, user)
    return PositionOut(position=await position_of(session, entry))


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
