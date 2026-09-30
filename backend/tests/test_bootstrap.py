"""What startup guarantees: a park that is never left without staff or tickets."""

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap import (
    DEFAULT_STAFF_PASSWORD,
    DEFAULT_STAFF_USERNAME,
    STARTING_ROLES,
    TICKETS_PER_ROLE,
    bootstrap,
)
from app.models import Ticket, User
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
