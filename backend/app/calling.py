"""The queue tick: what the worker does every few seconds, outside any request.

First the no-shows go: a called visitor whose grace period ran out loses their place, as
the SPEC says. Then the seats left free — neither taken (`people_inside`) nor promised to
someone already called — go to the next visitors in line, best fare first, then by
arrival (app.priority). Same transaction, same instant: a seat freed by a no-show is
handed on in the very same tick.
"""

import logging
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attraction, QueueEntry, Ticket
from app.priority import fare_rank

logger = logging.getLogger("app.calling")

# Any constant: two worker replicas must not run the same tick twice.
CALLING_LOCK = 20260930


async def drop_expired_calls(session: AsyncSession, now: datetime) -> int:
    """Removes from the queue every called visitor whose grace period has run out."""
    called = await session.scalars(select(QueueEntry).where(QueueEntry.is_ready.is_(True)))
    # `ready_expired` stays the single definition of "too late", shared with the API.
    expired = [entry for entry in called if entry.ready_expired(now)]
    for entry in expired:
        await session.delete(entry)
    await session.flush()
    return len(expired)


async def call_next_visitors(session: AsyncSession, now: datetime) -> int:
    """Marks as ready as many waiting visitors as there are free seats, best fare first."""
    called = 0
    for attraction in await session.scalars(select(Attraction).order_by(Attraction.id)):
        # No-shows are gone by now: every place still marked ready holds a seat.
        promised = await session.scalar(
            select(func.count())
            .select_from(QueueEntry)
            .where(QueueEntry.attraction_id == attraction.id, QueueEntry.is_ready.is_(True))
        )
        free = attraction.max_people - attraction.people_inside - promised
        if free <= 0:
            continue

        waiting = await session.scalars(
            select(QueueEntry)
            .join(Ticket)
            .where(QueueEntry.attraction_id == attraction.id, QueueEntry.is_ready.is_(False))
            .order_by(fare_rank(Ticket.role), QueueEntry.joined_at, QueueEntry.id)
            .limit(free)
        )
        for entry in waiting:
            entry.is_ready = True
            entry.ready_at = now
            called += 1
    return called


async def tick(session: AsyncSession) -> tuple[int, int]:
    """One pass of the worker. Returns (dropped, called). Commits."""
    await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": CALLING_LOCK})
    now = datetime.now()
    dropped = await drop_expired_calls(session, now)
    called = await call_next_visitors(session, now)
    await session.commit()
    if dropped or called:
        logger.info("dropped %d expired call(s), called %d visitor(s)", dropped, called)
    return dropped, called
