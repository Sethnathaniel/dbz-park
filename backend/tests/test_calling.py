"""The worker's tick: drop the no-shows, then call the next visitors when seats are free."""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.calling import tick
from app.models import Attraction, QueueEntry, Ticket
from tests.seed import (
    ENTRY_GOKU_READY,
    ENTRY_GOKU_WAITING,
    ENTRY_VEGETA_EXPIRED,
    ENTRY_VEGETA_WAITING,
    FREEZER_SHIP,
    KAIO_PALACE,
    KARIN_TOWER,
    TICKET_FREE,
    TICKET_GOKU_UNUSED,
)


async def fresh(session: AsyncSession, entry_id: int) -> QueueEntry | None:
    session.expire_all()
    return await session.get(QueueEntry, entry_id)


async def add_entry(session: AsyncSession, attraction_id: int, ticket_id: int, **fields) -> int:
    entry = QueueEntry(attraction_id=attraction_id, ticket_id=ticket_id, **fields)
    session.add(entry)
    await session.commit()
    return entry.id


class TestCallNextVisitors:
    async def test_calls_waiting_visitors_in_arrival_order_when_seats_are_free(
        self, session: AsyncSession
    ):
        # The Time Room has 50 seats, 12 taken, nobody called: both waiting visitors fit.
        _, called = await tick(session)

        assert called == 2
        goku = await fresh(session, ENTRY_GOKU_WAITING)
        assert goku.is_ready and goku.ready_at is not None
        assert (await fresh(session, ENTRY_VEGETA_WAITING)).is_ready

    async def test_calls_nobody_on_a_full_attraction(self, session: AsyncSession):
        # Freezer's ship: 2 seats, 2 people inside.
        waiting = await add_entry(
            session, FREEZER_SHIP, TICKET_GOKU_UNUSED, joined_at=datetime.now()
        )
        await tick(session)
        assert not (await fresh(session, waiting)).is_ready

    async def test_a_called_visitor_holds_a_seat(self, session: AsyncSession):
        # Kaio's palace, cut to 2 seats: goku is called and still in time, so he holds one.
        kaio = await session.get(Attraction, KAIO_PALACE)
        kaio.max_people = 2
        now = datetime.now()
        first = await add_entry(
            session, KAIO_PALACE, TICKET_GOKU_UNUSED, joined_at=now - timedelta(minutes=3)
        )
        second = await add_entry(
            session, KAIO_PALACE, TICKET_FREE, joined_at=now - timedelta(minutes=2)
        )

        await tick(session)

        # 2 seats − 1 promised to goku = 1: only the first in line is called.
        assert (await fresh(session, first)).is_ready
        assert not (await fresh(session, second)).is_ready


class TestDropExpiredCalls:
    async def test_removes_a_call_whose_grace_period_ran_out_and_keeps_the_others(
        self, session: AsyncSession
    ):
        dropped, _ = await tick(session)

        # vegeta was called ten minutes ago with 30 s to show up; goku, ten seconds ago.
        assert dropped == 1
        assert await fresh(session, ENTRY_VEGETA_EXPIRED) is None
        assert await fresh(session, ENTRY_GOKU_READY) is not None

    async def test_the_freed_seat_goes_to_the_next_in_line_in_the_same_tick(
        self, session: AsyncSession
    ):
        karin = await session.get(Attraction, KARIN_TOWER)
        karin.max_people = 1
        now = datetime.now()
        no_show = await add_entry(
            session,
            KARIN_TOWER,
            TICKET_GOKU_UNUSED,
            joined_at=now - timedelta(minutes=20),
            is_ready=True,
            ready_at=now - timedelta(minutes=6),
        )
        next_in_line = await add_entry(
            session, KARIN_TOWER, TICKET_FREE, joined_at=now - timedelta(minutes=10)
        )

        await tick(session)

        assert await fresh(session, no_show) is None
        assert (await fresh(session, next_in_line)).is_ready

    async def test_never_drops_a_place_that_was_not_called_however_long_it_waited(
        self, session: AsyncSession
    ):
        # On the full ship nobody gets called, so this place can only wait.
        patient = await add_entry(
            session,
            FREEZER_SHIP,
            TICKET_GOKU_UNUSED,
            joined_at=datetime.now() - timedelta(hours=3),
        )
        await tick(session)
        assert await fresh(session, patient) is not None



class TestCallingPriority:
    """Super Saiyan first, then Saiyan, then humans; inside a fare, first come first served."""

    async def one_seat_queue(self, session: AsyncSession, fares: list[tuple[str, int]]) -> list[int]:
        """Karin's tower cut to one seat, with a waiting place per (role, minutes ago)."""
        karin = await session.get(Attraction, KARIN_TOWER)
        karin.max_people = 1
        now = datetime.now()
        entries = []
        for index, (role, minutes_ago) in enumerate(fares):
            ticket = Ticket(numero=f"PRIO-{index}", role=role)
            session.add(ticket)
            await session.flush()
            entries.append(
                await add_entry(
                    session, KARIN_TOWER, ticket.id, joined_at=now - timedelta(minutes=minutes_ago)
                )
            )
        return entries

    async def called(self, session: AsyncSession, entries: list[int]) -> list[int]:
        await tick(session)
        return [entry for entry in entries if (await fresh(session, entry)).is_ready]

    async def test_a_super_saiyan_goes_before_everyone_even_arriving_last(
        self, session: AsyncSession
    ):
        normal, sayan, super_sayan = await self.one_seat_queue(
            session, [("normal", 30), ("sayan", 20), ("super_sayan", 10)]
        )
        assert await self.called(session, [normal, sayan, super_sayan]) == [super_sayan]

    async def test_without_a_super_saiyan_a_saiyan_goes_before_a_human(
        self, session: AsyncSession
    ):
        normal, sayan = await self.one_seat_queue(session, [("normal", 30), ("sayan", 10)])
        assert await self.called(session, [normal, sayan]) == [sayan]

    async def test_inside_a_fare_the_first_to_arrive_goes_first(self, session: AsyncSession):
        late, early = await self.one_seat_queue(
            session, [("super_sayan", 5), ("super_sayan", 15)]
        )
        assert await self.called(session, [late, early]) == [early]
