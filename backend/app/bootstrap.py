"""What the API makes sure exists before it serves its first request.

Both checks are all-or-nothing: they ask whether the table holds anything at all, so they
never argue with data created later. Empty park, usable park — that is the whole job.
"""

import logging
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ticket, User
from app.security import hash_password

logger = logging.getLogger("app.bootstrap")

DEFAULT_STAFF_USERNAME = "admin"
DEFAULT_STAFF_PASSWORD = "admin"
DEFAULT_STAFF_EMAIL = "admin@dbz-park.local"
# The fares an empty park starts with. Nothing else in the back knows this list.
STARTING_ROLES = ["super_sayan", "sayan", "normal"]
TICKETS_PER_ROLE = 10

# Any constant: two workers starting at once must not both try to create the same rows.
BOOTSTRAP_LOCK = 20260918


async def ensure_staff_account(session: AsyncSession) -> User | None:
    """Creates the default staff account when the park has none. Returns it, or None."""
    staff = await session.scalar(select(User).where(User.is_staff.is_(True)).limit(1))
    if staff is not None:
        return None

    taken = await session.scalar(select(User).where(User.username == DEFAULT_STAFF_USERNAME))
    if taken is not None:
        # Promoting it would hand the console to whoever registered that name first.
        logger.error(
            "no staff account, and the username %r is taken by a visitor: "
            "promote an account by hand, the console stays closed",
            DEFAULT_STAFF_USERNAME,
        )
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
        "no staff account found: created %r with the default password — change it",
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


async def bootstrap(session: AsyncSession) -> None:
    """Run once at startup, under a lock so several workers cannot race each other."""
    await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": BOOTSTRAP_LOCK})
    await ensure_staff_account(session)
    await ensure_tickets(session)
    await session.commit()
