"""The operations console, staff only.

`StaffUser` refuses a merely logged-in visitor with the same message as someone with no
token: nothing says the console exists.
"""

from fastapi import APIRouter, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admission import admit
from app.db import SessionDep
from app.dependencies import StaffUser
from app.errors import UNKNOWN_ENTRY, ApiError
from app.models import Attraction, QueueEntry, Ticket
from app.schemas.console import ConsoleAttractionOut, ConsoleReadyOut, ConsoleRowOut
from app.schemas.tickets import TicketOut

router = APIRouter(prefix="/console", tags=["console"])


async def any_entry(session: AsyncSession, entry_id: int) -> QueueEntry:
    entry = await session.get(QueueEntry, entry_id)
    if entry is None:
        raise ApiError(UNKNOWN_ENTRY)
    return entry


@router.get("/", response_model=list[ConsoleRowOut])
async def console_rows(staff: StaffUser, session: SessionDep) -> list[ConsoleRowOut]:
    """One row per attraction, including those where nobody is called."""
    attractions = await session.scalars(select(Attraction).order_by(Attraction.id))
    waiting = dict(
        (
            await session.execute(
                select(QueueEntry.attraction_id, func.count())
                .where(QueueEntry.is_ready.is_(False))
                .group_by(QueueEntry.attraction_id)
            )
        ).all()
    )
    called = await session.scalars(
        select(QueueEntry)
        .where(QueueEntry.is_ready.is_(True))
        .options(selectinload(QueueEntry.ticket).selectinload(Ticket.user))
        .order_by(QueueEntry.ready_at, QueueEntry.id)
    )
    ready_by_attraction: dict[int, list[ConsoleReadyOut]] = {}
    for entry in called:
        ready_by_attraction.setdefault(entry.attraction_id, []).append(
            ConsoleReadyOut(
                id=entry.id,
                username=entry.ticket.user.username if entry.ticket.user else "",
                ticket=TicketOut.model_validate(entry.ticket),
                ready_at=entry.ready_at,
                max_seconds_allowing_ready=entry.max_seconds_allowing_ready,
                ready_expired=entry.ready_expired(),
            )
        )

    return [
        ConsoleRowOut(
            attraction=ConsoleAttractionOut.model_validate(attraction, from_attributes=True),
            inside=attraction.people_inside,
            waiting=waiting.get(attraction.id, 0),
            ready=ready_by_attraction.get(attraction.id, []),
        )
        for attraction in attractions
    ]


@router.post("/entries/{entry_id}/accept/")
async def accept_entry(entry_id: int, staff: StaffUser, session: SessionDep) -> Response:
    """The visitor goes in, even past their grace period: the admin decides."""
    await admit(session, await any_entry(session, entry_id))
    await session.commit()
    return Response(status_code=200)


@router.post("/entries/{entry_id}/refuse/")
async def refuse_entry(entry_id: int, staff: StaffUser, session: SessionDep) -> Response:
    """The place is removed and the queue moves up."""
    await session.delete(await any_entry(session, entry_id))
    await session.commit()
    return Response(status_code=200)
