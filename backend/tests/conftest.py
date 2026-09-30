"""A throwaway Postgres database, recreated once and reseeded before every test.

It is a real Postgres, not SQLite: the schema uses a native enum and a reserved table
name, so testing on anything else would test something the park never runs.
"""

import asyncio
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db import get_session
from app.main import app
from app.models import Base, User
from app.security import create_token
from tests.seed import ADMIN, GOKU, VEGETA, reset_and_seed

settings = get_settings()

# A database of its own, next to the real one: tests never touch development data.
TEST_DATABASE = f"{settings.postgres_db}_test"
TEST_URL = settings.database_url.set(database=TEST_DATABASE)
MAINTENANCE_URL = settings.database_url.set(database="postgres")

async def _create_database() -> None:
    engine = create_async_engine(MAINTENANCE_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DATABASE}
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE}"'))
    await engine.dispose()

    engine = create_async_engine(TEST_URL)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def database() -> None:
    """Creates the test database and its tables, once for the whole run."""
    asyncio.run(_create_database())


@pytest.fixture(autouse=True)
def queues_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """Queues close at 19:00: without this, the suite would fail every evening."""
    monkeypatch.setattr(settings, "queue_closing_hour", 24)


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """A session on a freshly seeded database — one truncate per test, no leftovers."""
    engine = create_async_engine(TEST_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await reset_and_seed(session)
        yield session
    await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """The app, talking to the test session rather than to its own engine."""

    async def use_test_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = use_test_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        yield client
    app.dependency_overrides.clear()


def headers_for(user_id: int) -> dict[str, str]:
    """A valid Authorization header for that account."""
    return {"Authorization": f"Bearer {create_token(user_id)}"}


@pytest.fixture
def visitor() -> dict[str, str]:
    return headers_for(GOKU)


@pytest.fixture
def other_visitor() -> dict[str, str]:
    return headers_for(VEGETA)


@pytest.fixture
def staff() -> dict[str, str]:
    return headers_for(ADMIN)


@pytest.fixture
def forged() -> dict[str, str]:
    """A token signed with the wrong secret: the shape is right, the signature is not."""
    return {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.nope"}


async def count_users(session: AsyncSession) -> int:
    return await session.scalar(text("SELECT count(*) FROM \"user\"")) or 0


__all__ = ["headers_for", "count_users", "User"]
