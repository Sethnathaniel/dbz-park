"""What startup guarantees: a park never left without its admin, tickets or attractions."""

from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap import (
    DEFAULT_STAFF_PASSWORD,
    DEFAULT_STAFF_USERNAME,
    STARTING_ATTRACTIONS,
    STARTING_ROLES,
    TICKETS_PER_ROLE,
    bootstrap,
)
from app.calling import tick
from app.models import Attraction, QueueEntry, Ticket, User
from app.security import verify_password
from tests.seed import TABLES


async def empty(session: AsyncSession) -> None:
    await session.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    await session.commit()


class TestAdminAccount:
    async def test_creates_admin_even_when_another_staff_account_exists(
        self, session: AsyncSession
    ):
        await empty(session)
        # The check is on the name, not on "is there any staff": this one does not count.
        session.add(User(username="boss", password_hash="x", is_staff=True))
        await session.commit()

        await bootstrap(session)

        admin = await session.scalar(select(User).where(User.username == DEFAULT_STAFF_USERNAME))
        assert admin is not None and admin.is_staff
        assert verify_password(DEFAULT_STAFF_PASSWORD, admin.password_hash)

    async def test_leaves_an_existing_admin_and_its_password_alone(self, session: AsyncSession):
        # The seed already has `admin`, with another password: it must survive the restart.
        admin = await session.scalar(select(User).where(User.username == DEFAULT_STAFF_USERNAME))
        hash_before = admin.password_hash
        await bootstrap(session)

        session.expire_all()
        admin = await session.scalar(select(User).where(User.username == DEFAULT_STAFF_USERNAME))
        assert admin.password_hash == hash_before
        assert not verify_password(DEFAULT_STAFF_PASSWORD, admin.password_hash)
        assert await session.scalar(select(func.count()).select_from(User)) == 3

    async def test_does_not_promote_a_visitor_who_took_the_name(self, session: AsyncSession):
        await empty(session)
        session.add(User(username=DEFAULT_STAFF_USERNAME, password_hash="x", is_staff=False))
        await session.commit()

        await bootstrap(session)

        squatter = await session.scalar(
            select(User).where(User.username == DEFAULT_STAFF_USERNAME)
        )
        assert squatter is not None and not squatter.is_staff


class TestTickets:
    async def test_creates_ten_unassigned_tickets_per_role(self, session: AsyncSession):
        await empty(session)
        await bootstrap(session)

        tickets = (await session.scalars(select(Ticket))).all()
        assert len(tickets) == TICKETS_PER_ROLE * len(STARTING_ROLES)
        assert all(ticket.user_id is None for ticket in tickets)
        for role in STARTING_ROLES:
            assert sum(ticket.role == role for ticket in tickets) == TICKETS_PER_ROLE

    async def test_numbers_are_unique_and_sequential(self, session: AsyncSession):
        await empty(session)
        await bootstrap(session)

        numbers = sorted(t.numero for t in (await session.scalars(select(Ticket))).all())
        assert numbers[0] == "DBZ-0001"
        assert len(set(numbers)) == len(numbers) == TICKETS_PER_ROLE * len(STARTING_ROLES)

    async def test_does_nothing_when_the_park_already_sells_tickets(self, session: AsyncSession):
        before = await session.scalar(select(func.count()).select_from(Ticket))
        await bootstrap(session)
        assert await session.scalar(select(func.count()).select_from(Ticket)) == before


class TestAttractions:
    async def test_creates_the_four_starting_attractions_in_an_empty_park(
        self, session: AsyncSession
    ):
        await empty(session)
        await bootstrap(session)

        attractions = (await session.scalars(select(Attraction).order_by(Attraction.id))).all()
        assert [(a.name, a.max_people, a.avg_duration) for a in attractions] == STARTING_ATTRACTIONS
        assert all(a.people_inside == 0 for a in attractions)

    async def test_does_nothing_when_the_park_already_has_attractions(
        self, session: AsyncSession
    ):
        # The seed has its own four, and the Time Room holds 12 people: nothing may change.
        before = await session.scalar(select(func.count()).select_from(Attraction))
        await bootstrap(session)

        session.expire_all()
        assert await session.scalar(select(func.count()).select_from(Attraction)) == before
        time_room = await session.scalar(
            select(Attraction).where(Attraction.name == "La Salle du Temps")
        )
        assert time_room.people_inside == 12

    async def test_the_single_seat_attraction_calls_one_visitor_at_a_time(
        self, session: AsyncSession
    ):
        await empty(session)
        await bootstrap(session)
        karin = await session.scalar(select(Attraction).where(Attraction.max_people == 1))
        first, second = (await session.scalars(select(Ticket).order_by(Ticket.id).limit(2))).all()
        now = datetime.now()
        session.add_all(
            [
                QueueEntry(attraction_id=karin.id, ticket_id=first.id, joined_at=now),
                QueueEntry(attraction_id=karin.id, ticket_id=second.id, joined_at=now),
            ]
        )
        await session.commit()

        _, called = await tick(session)
        assert called == 1
