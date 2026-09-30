"""Letting someone into an attraction: shared by the visitor's validation and the console."""

from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ATTRACTION_FULL, ApiError
from app.models import Attraction, AttractionVisit, QueueEntry


async def admit(session: AsyncSession, entry: QueueEntry) -> None:
    """The place becomes a visit and the counter moves. The caller commits."""
    # Check and increment in one statement: two admissions cannot squeeze into the last seat.
    room = await session.scalar(
        update(Attraction)
        .where(Attraction.id == entry.attraction_id, Attraction.people_inside < Attraction.max_people)
        .values(people_inside=Attraction.people_inside + 1)
        .returning(Attraction.id)
    )
    if room is None:
        raise ApiError(ATTRACTION_FULL)

    session.add(
        AttractionVisit(
            attraction_id=entry.attraction_id, ticket_id=entry.ticket_id, entered_at=datetime.now()
        )
    )
    await session.delete(entry)
