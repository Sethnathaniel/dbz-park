"""Incidents: the admin stops an attraction, its queue pauses, and nobody loses their place."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.calling import tick
from app.models import Attraction, QueueEntry
from tests.seed import ENTRY_GOKU_READY, ENTRY_VEGETA_EXPIRED, KAIO_PALACE

BROKEN = {"reason": "Panne du manège, un technicien est en route."}


async def declare(client: AsyncClient, staff: dict[str, str], attraction_id: int = KAIO_PALACE):
    return await client.post(
        f"/console/attractions/{attraction_id}/incident/", json=BROKEN, headers=staff
    )


async def fresh(session: AsyncSession, model, id_: int):
    session.expire_all()
    return await session.get(model, id_)


class TestDeclareIncident:
    async def test_pauses_the_queue_and_sends_the_called_back_to_waiting(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        response = await declare(client, staff)
        assert response.status_code == 200

        kaio = await fresh(session, Attraction, KAIO_PALACE)
        assert kaio.incident_reason == BROKEN["reason"] and kaio.incident_since is not None
        # Goku was called and still in time: he waits again, his place intact.
        goku = await fresh(session, QueueEntry, ENTRY_GOKU_READY)
        assert not goku.is_ready and goku.ready_at is None
        # Vegeta had already missed his turn: the incident does not give it back.
        assert (await fresh(session, QueueEntry, ENTRY_VEGETA_EXPIRED)).is_ready

        # Kaio has twenty free seats, yet the worker calls nobody there.
        await tick(session)
        assert not (await fresh(session, QueueEntry, ENTRY_GOKU_READY)).is_ready

    async def test_refuses_an_empty_reason(self, client: AsyncClient, staff: dict[str, str]):
        response = await client.post(
            f"/console/attractions/{KAIO_PALACE}/incident/", json={"reason": "  "}, headers=staff
        )
        assert response.status_code == 400

    async def test_a_visitor_is_refused(self, client: AsyncClient, visitor: dict[str, str]):
        response = await declare(client, visitor)
        assert response.status_code == 400


class TestResumeAttraction:
    async def test_the_queue_moves_again(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        await declare(client, staff)
        response = await client.post(f"/console/attractions/{KAIO_PALACE}/resume/", headers=staff)
        assert response.status_code == 200

        kaio = await fresh(session, Attraction, KAIO_PALACE)
        assert kaio.incident_reason is None and kaio.incident_since is None
        # The next tick calls goku again: he kept his place through the incident.
        await tick(session)
        assert (await fresh(session, QueueEntry, ENTRY_GOKU_READY)).is_ready

    async def test_refuses_an_attraction_that_does_not_exist(
        self, client: AsyncClient, staff: dict[str, str]
    ):
        response = await client.post("/console/attractions/999/resume/", headers=staff)
        assert response.status_code == 400

    async def test_a_visitor_is_refused(self, client: AsyncClient, visitor: dict[str, str]):
        response = await client.post(
            f"/console/attractions/{KAIO_PALACE}/resume/", headers=visitor
        )
        assert response.status_code == 400


class TestWhileOutOfService:
    async def test_visitors_see_the_incident_and_the_paused_queue(
        self, client: AsyncClient, staff: dict[str, str], visitor: dict[str, str]
    ):
        await declare(client, staff)

        attractions = (await client.get("/attractions/", headers=visitor)).json()
        kaio = next(a for a in attractions if a["id"] == KAIO_PALACE)
        assert kaio["incident_reason"] == BROKEN["reason"]

        position = (
            await client.get(f"/queue/{ENTRY_GOKU_READY}/position/", headers=visitor)
        ).json()
        assert position == {"position": 1, "paused": True}

    async def test_nobody_gets_in(
        self, client: AsyncClient, session: AsyncSession, staff: dict[str, str]
    ):
        await declare(client, staff)
        # Even the admin cannot let in someone called before the incident.
        response = await client.post(
            f"/console/entries/{ENTRY_VEGETA_EXPIRED}/accept/", headers=staff
        )
        assert response.status_code == 400
        assert (await fresh(session, Attraction, KAIO_PALACE)).people_inside == 0
