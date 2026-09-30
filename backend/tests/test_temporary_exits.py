"""TEMPORARY — visitors let out after 30 s inside, until the park has an exit route."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calling import tick
from app.models import Attraction, AttractionVisit, QueueEntry
from app.temporary_exits import VISIT_SECONDS, release_finished_visits
from tests.seed import FREEZER_SHIP, TICKET_GOKU_UNUSED

# The seed's only visit: vegeta, inside Freezer's ship (2 seats, counter at 2).
SEED_VISIT = 1


async def people_inside(session: AsyncSession, attraction_id: int) -> int:
    session.expire_all()
    return (await session.get(Attraction, attraction_id)).people_inside


async def entered(session: AsyncSession, seconds_ago: int) -> None:
    visit = await session.get(AttractionVisit, SEED_VISIT)
    visit.entered_at = datetime.now() - timedelta(seconds=seconds_ago)
    await session.commit()


class TestReleaseFinishedVisits:
    async def test_lets_out_a_visitor_inside_for_30_seconds_or_more(self, session: AsyncSession):
        await entered(session, VISIT_SECONDS + 1)

        assert await release_finished_visits(session) == 1
        assert await session.get(AttractionVisit, SEED_VISIT) is None
        assert await people_inside(session, FREEZER_SHIP) == 1

    async def test_keeps_a_visitor_who_just_went_in(self, session: AsyncSession):
        await entered(session, VISIT_SECONDS - 5)

        assert await release_finished_visits(session) == 0
        assert await session.get(AttractionVisit, SEED_VISIT) is not None
        assert await people_inside(session, FREEZER_SHIP) == 2

    async def test_the_seat_it_frees_lets_the_queue_move_on(self, session: AsyncSession):
        # Three seats: two people inside plus one already called, so nobody else fits yet.
        (await session.get(Attraction, FREEZER_SHIP)).max_people = 3
        session.add(
            QueueEntry(
                attraction_id=FREEZER_SHIP, ticket_id=TICKET_GOKU_UNUSED, joined_at=datetime.now()
            )
        )
        await session.commit()
        waiting = await session.scalar(
            select(QueueEntry.id).where(QueueEntry.ticket_id == TICKET_GOKU_UNUSED)
        )

        await tick(session)
        session.expire_all()
        assert not (await session.get(QueueEntry, waiting)).is_ready

        await entered(session, VISIT_SECONDS)
        await release_finished_visits(session)
        await tick(session)

        session.expire_all()
        assert (await session.get(QueueEntry, waiting)).is_ready
