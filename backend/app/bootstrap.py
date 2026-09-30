"""What the API makes sure exists before it serves its first request.

Tickets and attractions are all-or-nothing: the table is filled only when it holds
nothing at all, so it never argues with data created later. Empty park, usable park —
that is the whole job.
"""

import logging
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attraction, Ticket, User
from app.security import hash_password

logger = logging.getLogger("app.bootstrap")

DEFAULT_STAFF_USERNAME = "admin"
DEFAULT_STAFF_PASSWORD = "password"
DEFAULT_STAFF_EMAIL = "admin@dbz-park.local"
# The fares an empty park starts with. Nothing else in the back knows this list.
STARTING_ROLES = ["super_sayan", "sayan", "normal"]
TICKETS_PER_ROLE = 10

# (name, max_people, avg_duration in seconds). The last one fits a single visitor.
STARTING_ATTRACTIONS = [
    ("La Salle du Temps", 50, 120),
    ("Le Vaisseau de Freezer", 2, 180),
    ("Le Palais de Kaio", 20, 90),
    ("La Tour de Karin", 1, 60),
]

# Any constant: two workers starting at once must not both try to create the same rows.
BOOTSTRAP_LOCK = 20260918


async def ensure_admin_account(session: AsyncSession) -> User | None:
    """Creates the `admin` staff account when no user has that name. Returns it, or None."""
    existing = await session.scalar(select(User).where(User.username == DEFAULT_STAFF_USERNAME))
    if existing is not None:
        if not existing.is_staff:
            # Left as it is: promoting it would hand the console to whoever took the name.
            logger.warning("%r exists but is not staff: left untouched", DEFAULT_STAFF_USERNAME)
        return None

    user = User(
        username=DEFAULT_STAFF_USERNAME,
        email=DEFAULT_STAFF_EMAIL,
        password_hash=hash_password(DEFAULT_STAFF_PASSWORD),
        is_staff=True,
    )
    session.add(user)
    await session.flush()
    logger.warning(
        "no %r account found: created it with the default password — change it",
        DEFAULT_STAFF_USERNAME,
    )
    return user


async def ensure_tickets(session: AsyncSession) -> list[Ticket]:
    """Fills an empty park with unassigned tickets, ten per role. Returns what it created."""
    if await session.scalar(select(func.count()).select_from(Ticket)):
        return []

    now = datetime.now()
    tickets = [
        Ticket(user_id=None, numero=f"DBZ-{number:04d}", role=role, created_at=now)
        for number, role in enumerate(
            (role for role in STARTING_ROLES for _ in range(TICKETS_PER_ROLE)), start=1
        )
    ]
    session.add_all(tickets)
    await session.flush()
    logger.info("no ticket found: created %d, %d per role", len(tickets), TICKETS_PER_ROLE)
    return tickets


async def ensure_attractions(session: AsyncSession) -> list[Attraction]:
    """Fills a park with no attraction with the starting four. Returns what it created."""
    if await session.scalar(select(func.count()).select_from(Attraction)):
        return []

    attractions = [
        Attraction(name=name, max_people=max_people, avg_duration=avg_duration, people_inside=0)
        for name, max_people, avg_duration in STARTING_ATTRACTIONS
    ]
    session.add_all(attractions)
    await session.flush()
    logger.info("no attraction found: created %d", len(attractions))
    return attractions


async def bootstrap(session: AsyncSession) -> None:
    """Run once at startup, under a lock so several workers cannot race each other."""
    await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": BOOTSTRAP_LOCK})
    await ensure_admin_account(session)
    await ensure_tickets(session)
    await ensure_attractions(session)
    await session.commit()
