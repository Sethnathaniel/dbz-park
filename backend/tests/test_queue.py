"""Places held in a queue: position, withdrawal, validation."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AttractionVisit, QueueEntry, Ticket
from tests.seed import (
    ENTRY_GOKU_READY,
    ENTRY_GOKU_WAITING,
    ENTRY_VEGETA_EXPIRED,
    ENTRY_VEGETA_WAITING,
    FREEZER_SHIP,
    KAIO_PALACE,
    TICKET_VEGETA,
)


async def people_inside(client: AsyncClient, headers: dict[str, str], attraction_id: int) -> int:
    attractions = (await client.get("/attractions/", headers=headers)).json()
    return next(a["people_inside"] for a in attractions if a["id"] == attraction_id)


class TestMyQueue:
    """`GET /queue/` — the caller's places and visits, and nobody else's."""

    async def test_lists_the_callers_places_and_visits_only(
        self, client: AsyncClient, other_visitor: dict[str, str]
    ):
        response = await client.get("/queue/", headers=other_visitor)
        assert response.status_code == 200
        body = response.json()
        # vegeta: waiting second on the Time Room, missed turn at Kaio, inside Freezer's ship.
        assert {e["id"]: (e["position"], e["ready_expired"]) for e in body["entries"]} == {
            ENTRY_VEGETA_WAITING: (2, False),
            ENTRY_VEGETA_EXPIRED: (0, True),
        }
        assert [v["attraction_id"] for v in body["visits"]] == [FREEZER_SHIP]

    async def test_refuses_without_a_token(self, client: AsyncClient):
        response = await client.get("/queue/")
        assert response.status_code == 400

    async def test_refuses_a_forged_token(self, client: AsyncClient, forged: dict[str, str]):
        response = await client.get("/queue/", headers=forged)
        assert response.status_code == 400


class TestPosition:
    async def test_a_better_fare_is_ahead_whoever_came_first(
        self,
        client: AsyncClient,
        session: AsyncSession,
        visitor: dict[str, str],
        other_visitor: dict[str, str],
    ):
        # goku joined the Time Room first, but vegeta's ticket becomes a Super Saiyan one.
        (await session.get(Ticket, TICKET_VEGETA)).role = "super_sayan"
        await session.commit()

        goku = await client.get(f"/queue/{ENTRY_GOKU_WAITING}/position/", headers=visitor)
        vegeta = await client.get(f"/queue/{ENTRY_VEGETA_WAITING}/position/", headers=other_visitor)
        assert goku.status_code == vegeta.status_code == 200
        assert (vegeta.json(), goku.json()) == ({"position": 1}, {"position": 2})

    async def test_a_place_that_is_not_yours_answers_like_a_missing_one(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        not_mine = await client.get(f"/queue/{ENTRY_VEGETA_WAITING}/position/", headers=visitor)
        missing = await client.get("/queue/999/position/", headers=visitor)
        assert not_mine.status_code == missing.status_code == 400
        assert not_mine.json()["detail"] == missing.json()["detail"]

    async def test_refuses_without_a_token(self, client: AsyncClient):
        response = await client.get(f"/queue/{ENTRY_GOKU_WAITING}/position/")
        assert response.status_code == 400


class TestLeaveQueue:
    async def test_releases_the_place_and_the_queue_moves_up(
        self, client: AsyncClient, visitor: dict[str, str], other_visitor: dict[str, str]
    ):
        response = await client.post(f"/queue/{ENTRY_GOKU_WAITING}/leave/", headers=visitor)
        assert response.status_code == 200

        vegeta = await client.get(f"/queue/{ENTRY_VEGETA_WAITING}/position/", headers=other_visitor)
        assert vegeta.json() == {"position": 1}

    async def test_cannot_release_someone_elses_place(
        self, client: AsyncClient, session: AsyncSession, visitor: dict[str, str]
    ):
        response = await client.post(f"/queue/{ENTRY_VEGETA_WAITING}/leave/", headers=visitor)
        assert response.status_code == 400
        assert await session.get(QueueEntry, ENTRY_VEGETA_WAITING) is not None

    async def test_refuses_without_a_token(self, client: AsyncClient):
        response = await client.post(f"/queue/{ENTRY_GOKU_WAITING}/leave/")
        assert response.status_code == 400


class TestValidateQueueEntry:
    async def test_a_called_visitor_goes_in(
        self, client: AsyncClient, session: AsyncSession, visitor: dict[str, str]
    ):
        response = await client.post(f"/queue/{ENTRY_GOKU_READY}/validate/", headers=visitor)
        assert response.status_code == 200

        session.expire_all()
        assert await session.get(QueueEntry, ENTRY_GOKU_READY) is None
        assert await session.get(AttractionVisit, 2) is not None
        assert await people_inside(client, visitor, KAIO_PALACE) == 1

    async def test_refuses_a_turn_that_has_not_come(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        response = await client.post(f"/queue/{ENTRY_GOKU_WAITING}/validate/", headers=visitor)
        assert response.status_code == 400
        assert "pas encore" in response.json()["detail"]

    async def test_refuses_a_turn_that_has_passed(
        self, client: AsyncClient, other_visitor: dict[str, str]
    ):
        response = await client.post(
            f"/queue/{ENTRY_VEGETA_EXPIRED}/validate/", headers=other_visitor
        )
        assert response.status_code == 400
        assert "passé" in response.json()["detail"]
