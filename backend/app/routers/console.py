"""The operations console, staff only.

`StaffUser` refuses a merely logged-in visitor with the same message as someone with no
token: nothing says the console exists.
"""

from datetime import datetime

from fastapi import APIRouter, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admission import admit
from app.db import SessionDep
from app.dependencies import StaffUser
from app.errors import UNKNOWN_ATTRACTION, UNKNOWN_ENTRY, ApiError
from app.models import Attraction, QueueEntry, Ticket
from app.schemas.console import ConsoleAttractionOut, ConsoleReadyOut, ConsoleRowOut, IncidentIn
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


async def any_attraction(session: AsyncSession, attraction_id: int) -> Attraction:
    attraction = await session.get(Attraction, attraction_id)
    if attraction is None:
        raise ApiError(UNKNOWN_ATTRACTION)
    return attraction


@router.post("/attractions/{attraction_id}/incident/")
async def declare_incident(
    attraction_id: int, incident: IncidentIn, staff: StaffUser, session: SessionDep
) -> Response:
    """Stops the attraction: its queue pauses, and nobody loses their place.

    Visitors called and still in time go back to waiting. Their arrival is untouched, so
    they are first again when it reopens — rather than running out their 30 seconds
    meanwhile. Those already too late stay as they are: the worker removes them as usual.
    Declaring again only updates the reason.
    """
    attraction = await any_attraction(session, attraction_id)
    if not attraction.out_of_service:
        attraction.incident_since = datetime.now()
    attraction.incident_reason = incident.reason

    called = await session.scalars(
        select(QueueEntry).where(
            QueueEntry.attraction_id == attraction_id, QueueEntry.is_ready.is_(True)
        )
    )
    for entry in called:
        if not entry.ready_expired():
            entry.is_ready = False
            entry.ready_at = None
    await session.commit()
    return Response(status_code=200)


@router.post("/attractions/{attraction_id}/resume/")
async def resume_attraction(attraction_id: int, staff: StaffUser, session: SessionDep) -> Response:
    """Back to normal: the worker calls the queue again on its next tick."""
    attraction = await any_attraction(session, attraction_id)
    attraction.incident_reason = None
    attraction.incident_since = None
    await session.commit()
    return Response(status_code=200)
