"""The rows every test starts from.

Ids are deterministic: the reset truncates with `RESTART IDENTITY`, so inserting in this
order always yields the same ids, and a test can name `TICKET_FREE` instead of a number.
"""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attraction, AttractionVisit, QueueEntry, Ticket, User
from app.security import hash_password

PASSWORD = "kamehameha"

GOKU, VEGETA, ADMIN = 1, 2, 3
TICKET_GOKU_SUPER, TICKET_GOKU_NORMAL, TICKET_FREE = 1, 2, 3
TICKET_VEGETA, TICKET_VEGETA_SECOND, TICKET_GOKU_THIRD, TICKET_GOKU_UNUSED = 4, 5, 6, 7
TIME_ROOM, FREEZER_SHIP, KAIO_PALACE, KARIN_TOWER = 1, 2, 3, 4
ENTRY_GOKU_WAITING, ENTRY_VEGETA_WAITING = 1, 2
ENTRY_GOKU_READY, ENTRY_VEGETA_EXPIRED = 3, 4
ENTRY_READY_ON_FULL = 5

TABLES = '"user", ticket, attraction, queue_entry, attraction_visit'


async def reset_and_seed(session: AsyncSession) -> None:
    from sqlalchemy import text

    await session.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))

    now = datetime.now()
    session.add_all(
        [
            User(username="goku", email="goku@dbz.fr", password_hash=hash_password(PASSWORD)),
            User(username="vegeta", email="vegeta@dbz.fr", password_hash=hash_password(PASSWORD)),
            User(
                username="admin",
                email="admin@dbz.fr",
                password_hash=hash_password(PASSWORD),
                is_staff=True,
            ),
        ]
    )
    await session.flush()

    session.add_all(
        [
            Ticket(user_id=GOKU, numero="DBZ-0001", role="super_sayan"),
            Ticket(user_id=GOKU, numero="DBZ-0002", role="normal"),
            # Nobody holds this one: it is what `POST /tickets/assign/` claims.
            Ticket(user_id=None, numero="DBZ-0003", role="sayan"),
            Ticket(user_id=VEGETA, numero="DBZ-0004", role="normal"),
            Ticket(user_id=VEGETA, numero="DBZ-0005", role="normal"),
            Ticket(user_id=GOKU, numero="DBZ-0006", role="normal"),
            # In no queue and no visit: the one `join` can spend.
            Ticket(user_id=GOKU, numero="DBZ-0007", role="sayan"),
        ]
    )
    session.add_all(
        [
            Attraction(name="La Salle du Temps", max_people=50, avg_duration=120, people_inside=12),
            # Deliberately full: `people_inside` == `max_people`.
            Attraction(name="Le Vaisseau de Freezer", max_people=2, avg_duration=180, people_inside=2),
            Attraction(name="Le Palais de Kaio", max_people=20, avg_duration=60, people_inside=0),
            # Nobody queues here: somewhere to join from scratch.
            Attraction(name="La Tour de Karin", max_people=10, avg_duration=90, people_inside=0),
        ]
    )
    await session.flush()

    session.add_all(
        [
            # Two people waiting on the Time Room, goku ahead of vegeta.
            QueueEntry(
                attraction_id=TIME_ROOM,
                ticket_id=TICKET_GOKU_NORMAL,
                joined_at=now - timedelta(minutes=20),
            ),
            QueueEntry(
                attraction_id=TIME_ROOM,
                ticket_id=TICKET_VEGETA,
                joined_at=now - timedelta(minutes=10),
            ),
            # Called ten seconds ago: still inside the 30 s grace period.
            QueueEntry(
                attraction_id=KAIO_PALACE,
                ticket_id=TICKET_GOKU_SUPER,
                joined_at=now - timedelta(minutes=30),
                is_ready=True,
                ready_at=now - timedelta(seconds=10),
            ),
            # Called ten minutes ago: the turn was missed.
            QueueEntry(
                attraction_id=KAIO_PALACE,
                ticket_id=TICKET_VEGETA_SECOND,
                joined_at=now - timedelta(minutes=35),
                is_ready=True,
                ready_at=now - timedelta(minutes=10),
            ),
            # Called on the attraction that has no room left: the admin cannot let them in.
            QueueEntry(
                attraction_id=FREEZER_SHIP,
                ticket_id=TICKET_GOKU_THIRD,
                joined_at=now - timedelta(minutes=15),
                is_ready=True,
                ready_at=now - timedelta(seconds=10),
            ),
        ]
    )
    session.add_all(
        [AttractionVisit(attraction_id=FREEZER_SHIP, ticket_id=TICKET_VEGETA, entered_at=now)]
    )
    await session.commit()
