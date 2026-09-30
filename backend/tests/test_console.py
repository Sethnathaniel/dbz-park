"""The operations console: staff only, and it must not admit that it exists."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QueueEntry
from tests.seed import ENTRY_GOKU_READY, ENTRY_READY_ON_FULL, ENTRY_VEGETA_EXPIRED, KAIO_PALACE


class TestConsoleRows:
    async def test_lists_every_attraction_with_who_has_been_called(
        self, client: AsyncClient, staff: dict[str, str]
    ):
        response = await client.get("/console/", headers=staff)
        assert response.status_code == 200
        rows = {row["attraction"]["name"]: row for row in response.json()}

        # An attraction with nobody called is still returned, with an empty list.
        assert {name: len(row["ready"]) for name, row in rows.items()} == {
            "La Salle du Temps": 0,
            "Le Vaisseau de Freezer": 1,
            "Le Palais de Kaio": 2,
            "La Tour de Karin": 0,
        }
        assert rows["La Salle du Temps"]["waiting"] == 2
        kaio = {r["username"]: r["ready_expired"] for r in rows["Le Palais de Kaio"]["ready"]}
        assert kaio == {"goku": False, "vegeta": True}

    async def test_a_visitor_is_refused(self, client: AsyncClient, visitor: dict[str, str]):
        response = await client.get("/console/", headers=visitor)
        assert response.status_code == 400

    async def test_refuses_without_a_token(self, client: AsyncClient):
        response = await client.get("/console/")
        assert response.status_code == 400


class TestAcceptEntry:
    async def test_lets_in_even_a_visitor_whose_turn_has_passed(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        response = await client.post(
            f"/console/entries/{ENTRY_VEGETA_EXPIRED}/accept/", headers=staff
        )
        assert response.status_code == 200

        attractions = (await client.get("/attractions/", headers=staff)).json()
        assert next(a for a in attractions if a["id"] == KAIO_PALACE)["people_inside"] == 1

    async def test_refuses_when_the_attraction_is_full(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        response = await client.post(
            f"/console/entries/{ENTRY_READY_ON_FULL}/accept/", headers=staff
        )
        assert response.status_code == 400
        # Refused means untouched: the place is still waiting for a seat.
        assert await session.get(QueueEntry, ENTRY_READY_ON_FULL) is not None

    async def test_a_visitor_cannot_accept_their_own_place(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        response = await client.post(
            f"/console/entries/{ENTRY_GOKU_READY}/accept/", headers=visitor
        )
        assert response.status_code == 400


class TestRefuseEntry:
    async def test_removes_the_place(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        response = await client.post(
            f"/console/entries/{ENTRY_GOKU_READY}/refuse/", headers=staff
        )
        assert response.status_code == 200
        session.expire_all()
        assert await session.get(QueueEntry, ENTRY_GOKU_READY) is None

    async def test_refuses_a_place_that_does_not_exist(
        self, client: AsyncClient, staff: dict[str, str]
    ):
        response = await client.post("/console/entries/999/refuse/", headers=staff)
        assert response.status_code == 400

    async def test_a_visitor_is_refused(self, client: AsyncClient, visitor: dict[str, str]):
        response = await client.post(
            f"/console/entries/{ENTRY_GOKU_READY}/refuse/", headers=visitor
        )
        assert response.status_code == 400
