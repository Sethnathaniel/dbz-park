"""Account management: the staff finds, edits and deletes accounts, and switches tickets
off or back on. An admin must never be able to lock themself out."""

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QueueEntry, Ticket, User
from tests.seed import (
    ADMIN,
    ENTRY_GOKU_READY,
    GOKU,
    KARIN_TOWER,
    TICKET_FREE,
    TICKET_GOKU_SUPER,
    TICKET_GOKU_UNUSED,
    VEGETA,
)


async def fresh(session: AsyncSession, model, id_: int):
    session.expire_all()
    return await session.get(model, id_)


class TestSearchAccounts:
    async def test_finds_an_account_by_part_of_its_name(
        self, client: AsyncClient, staff: dict[str, str]
    ):
        response = await client.get("/console/users/", params={"search": "GOK"}, headers=staff)
        assert response.status_code == 200
        [goku] = response.json()
        assert goku["username"] == "goku" and goku["email"] == "goku@dbz.fr"
        assert [t["numero"] for t in goku["tickets"]] == [
            "DBZ-0001", "DBZ-0002", "DBZ-0006", "DBZ-0007",
        ]

    async def test_an_empty_search_lists_everyone_alphabetically(
        self, client: AsyncClient, staff: dict[str, str]
    ):
        response = await client.get("/console/users/", headers=staff)
        assert [a["username"] for a in response.json()] == ["admin", "goku", "vegeta"]

    async def test_a_visitor_is_refused(self, client: AsyncClient, visitor: dict[str, str]):
        response = await client.get("/console/users/", headers=visitor)
        assert response.status_code == 400


class TestUpdateAccount:
    async def test_renames_and_gives_staff_rights(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        response = await client.post(
            f"/console/users/{VEGETA}/",
            json={"username": "prince_vegeta", "email": "prince@dbz.fr", "is_staff": True},
            headers=staff,
        )
        assert response.status_code == 200
        vegeta = await fresh(session, User, VEGETA)
        assert (vegeta.username, vegeta.email, vegeta.is_staff) == (
            "prince_vegeta", "prince@dbz.fr", True,
        )

    async def test_refuses_a_name_already_taken(
        self, client: AsyncClient, staff: dict[str, str]
    ):
        response = await client.post(
            f"/console/users/{VEGETA}/",
            json={"username": "goku", "email": "vegeta@dbz.fr", "is_staff": False},
            headers=staff,
        )
        assert response.status_code == 400

    async def test_an_admin_cannot_drop_their_own_rights(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        response = await client.post(
            f"/console/users/{ADMIN}/",
            json={"username": "admin", "email": "admin@dbz.fr", "is_staff": False},
            headers=staff,
        )
        assert response.status_code == 400
        assert (await fresh(session, User, ADMIN)).is_staff


class TestDeleteAccount:
    async def test_deletes_the_account_and_frees_its_tickets(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        response = await client.post(f"/console/users/{GOKU}/delete/", headers=staff)
        assert response.status_code == 200

        assert await fresh(session, User, GOKU) is None
        # His tickets stay in the park, with nobody holding them…
        assert (await fresh(session, Ticket, TICKET_GOKU_SUPER)).user_id is None
        # …and his places in the queues are gone.
        assert await fresh(session, QueueEntry, ENTRY_GOKU_READY) is None

    async def test_an_admin_cannot_delete_their_own_account(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        response = await client.post(f"/console/users/{ADMIN}/delete/", headers=staff)
        assert response.status_code == 400
        assert await fresh(session, User, ADMIN) is not None

    async def test_a_visitor_is_refused(
        self, client: AsyncClient, session: AsyncSession, visitor: dict[str, str]
    ):
        response = await client.post(f"/console/users/{VEGETA}/delete/", headers=visitor)
        assert response.status_code == 400
        assert await session.scalar(select(func.count()).select_from(User)) == 3


class TestTicketValidity:
    async def test_a_revoked_ticket_leaves_its_queue_and_cannot_join_another(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str], visitor
    ):
        response = await client.post(f"/console/tickets/{TICKET_GOKU_SUPER}/revoke/", headers=staff)
        assert response.status_code == 200
        assert response.json()["is_valid"] is False
        assert await fresh(session, QueueEntry, ENTRY_GOKU_READY) is None

        # Goku's only free ticket switched off too: nothing left to join with.
        await client.post(f"/console/tickets/{TICKET_GOKU_UNUSED}/revoke/", headers=staff)
        joined = await client.post(f"/attractions/{KARIN_TOWER}/queue/join/", headers=visitor)
        assert joined.status_code == 400

    async def test_a_revoked_ticket_cannot_be_claimed_until_restored(
        self, client: AsyncClient, staff: dict[str, str], other_visitor: dict[str, str]
    ):
        await client.post(f"/console/tickets/{TICKET_FREE}/revoke/", headers=staff)
        claim = {"numero": "DBZ-0003"}
        refused = await client.post("/tickets/assign/", json=claim, headers=other_visitor)
        assert refused.status_code == 400

        restored = await client.post(f"/console/tickets/{TICKET_FREE}/restore/", headers=staff)
        assert restored.json()["is_valid"] is True
        accepted = await client.post("/tickets/assign/", json=claim, headers=other_visitor)
        assert accepted.status_code == 200

    async def test_a_visitor_cannot_revoke_a_ticket(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        response = await client.post(f"/console/tickets/{TICKET_FREE}/revoke/", headers=visitor)
        assert response.status_code == 400
