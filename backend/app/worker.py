"""The Celery worker: runs the queue tick every few seconds, outside the HTTP cycle.

Beat fires the task on a schedule, the worker runs it:
    celery -A app.worker worker --beat --concurrency=1 --loglevel=info
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.calling import tick
from app.config import get_settings

settings = get_settings()

T = TypeVar("T")

# TEMPORARY: app.temporary_exits lets visitors out after 30 s, until an exit route exists.
celery = Celery("dbz_park", broker=settings.redis_url, include=["app.temporary_exits"])
celery.conf.beat_schedule = {
    "queue-tick": {
        "task": "app.worker.queue_tick_task",
        "schedule": settings.calling_interval_seconds,
        # A tick that could not run in time is dropped, not queued behind the next one.
        "options": {"expires": settings.calling_interval_seconds},
    },
    "temporary-exits": {
        "task": "app.temporary_exits.release_finished_visits_task",
        "schedule": settings.calling_interval_seconds,
        "options": {"expires": settings.calling_interval_seconds},
    },
}


def run_with_session(work: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Runs `work` in a fresh event loop, on a fresh session: what every task needs."""

    async def run() -> T:
        # Each task gets its own loop, so a connection pooled by the previous one is unusable.
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as session:
                return await work(session)
        finally:
            await engine.dispose()

    return asyncio.run(run())


@celery.task(name="app.worker.queue_tick_task")
def queue_tick_task() -> tuple[int, int]:
    """Drops the no-shows, then calls the next visitors: see app.calling."""
    return run_with_session(tick)
