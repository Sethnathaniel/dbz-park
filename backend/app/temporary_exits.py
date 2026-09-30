"""TEMPORARY — lets visitors out of an attraction once they have been inside long enough.

Stands in for the exit route the park does not have yet: without it `people_inside` only
grows. A visit of VISIT_SECONDS or more is treated as a finished ride. To remove it:
delete this file, and its two lines in app/worker.py (`include` and the beat entry).
"""

import logging
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attraction, AttractionVisit
from app.worker import celery, run_with_session

logger = logging.getLogger("app.temporary_exits")

VISIT_SECONDS = 30


async def release_finished_visits(session: AsyncSession) -> int:
    """Deletes the visits of VISIT_SECONDS or more and lowers each counter. Commits."""
    cutoff = datetime.now() - timedelta(seconds=VISIT_SECONDS)
    finished = (
        await session.scalars(
            delete(AttractionVisit)
            .where(AttractionVisit.entered_at <= cutoff)
            .returning(AttractionVisit.attraction_id),
            execution_options={"synchronize_session": False},
        )
    ).all()
    for attraction_id, leaving in Counter(finished).items():
        # In one statement, and never below zero if the counter had drifted from the visits.
        await session.execute(
            update(Attraction)
            .where(Attraction.id == attraction_id)
            .values(people_inside=func.greatest(Attraction.people_inside - leaving, 0))
        )
    await session.commit()
    if finished:
        logger.info("let %d visitor(s) out", len(finished))
    return len(finished)


@celery.task(name="app.temporary_exits.release_finished_visits_task")
def release_finished_visits_task() -> int:
    return run_with_session(release_finished_visits)
