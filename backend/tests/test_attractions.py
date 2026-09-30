"""The catalogue, and joining a queue."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import QueueEntry
from tests.seed import KARIN_TOWER, TICKET_GOKU_UNUSED, TIME_ROOM

# Exactly what `GET /attractions/` publishes: the attraction, and nothing about the caller.
ATTRACTION_FIELDS = {"id", "name", "photo_url", "max_people", "people_inside", "avg_duration"}


class TestListAttractions:
    async def test_returns_the_attractions_and_only_their_own_fields(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        response = await client.get("/attractions/", headers=visitor)
        assert response.status_code == 200
        attractions = response.json()
        assert [a["name"] for a in attractions] == [
            "La Salle du Temps",
            "Le Vaisseau de Freezer",
            "Le Palais de Kaio",
            "La Tour de Karin",
        ]
        assert set(attractions[0]) == ATTRACTION_FIELDS
        assert attractions[0]["avg_duration"] == 120
        assert attractions[0]["people_inside"] == 12

    async def test_refuses_without_a_token(self, client: AsyncClient):
        response = await client.get("/attractions/")
        assert response.status_code == 400

    async def test_refuses_a_forged_token(self, client: AsyncClient, forged: dict[str, str]):
        response = await client.get("/attractions/", headers=forged)
        assert response.status_code == 400


class TestJoinQueue:
    async def test_takes_a_place_with_the_first_free_ticket(
        self, client: AsyncClient, session: AsyncSession, visitor: dict[str, str]
    ):
        response = await client.post(f"/attractions/{KARIN_TOWER}/queue/join/", headers=visitor)
        assert response.status_code == 200

        entry = await session.scalar(select(QueueEntry).where(QueueEntry.attraction_id == KARIN_TOWER))
        # goku's three other tickets are all engaged: only DBZ-0007 was left.
        assert entry is not None and entry.ticket_id == TICKET_GOKU_UNUSED

    async def test_refuses_a_second_place_on_the_same_attraction(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        response = await client.post(f"/attractions/{TIME_ROOM}/queue/join/", headers=visitor)
        assert response.status_code == 400

    async def test_refuses_once_the_queues_are_closed(
        self, client: AsyncClient, visitor: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(get_settings(), "queue_closing_hour", 0)
        response = await client.post(f"/attractions/{KARIN_TOWER}/queue/join/", headers=visitor)
        assert response.status_code == 400
        assert "fermées" in response.json()["detail"]
