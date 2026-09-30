"""Tickets: one staff-wide listing, one per-visitor listing, and the two writes."""

from httpx import AsyncClient

from tests.seed import GOKU


class TestListAllTickets:
    """`GET /tickets/` — the one response that ties a ticket to a name."""

    async def test_staff_sees_every_ticket_with_its_holder(
        self, client: AsyncClient, staff: dict[str, str]
    ):
        response = await client.get("/tickets/", headers=staff)
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) == 7
        assert {t["numero"]: (t["user"] or {}).get("username") for t in tickets} == {
            "DBZ-0001": "goku",
            "DBZ-0002": "goku",
            "DBZ-0003": None,
            "DBZ-0004": "vegeta",
            "DBZ-0005": "vegeta",
            "DBZ-0006": "goku",
            "DBZ-0007": "goku",
        }

    async def test_a_visitor_is_refused(self, client: AsyncClient, visitor: dict[str, str]):
        response = await client.get("/tickets/", headers=visitor)
        assert response.status_code == 400

    async def test_a_visitor_is_refused_exactly_like_a_stranger(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        logged_in = await client.get("/tickets/", headers=visitor)
        anonymous = await client.get("/tickets/")
        # Nothing may hint that the route exists, let alone what it would take to open it.
        assert logged_in.json()["detail"] == anonymous.json()["detail"]


class TestListUserTickets:
    """`GET /user/<id>/tickets/` — readable by that visitor, or by staff."""

    async def test_a_visitor_reads_their_own(self, client: AsyncClient, visitor: dict[str, str]):
        response = await client.get(f"/user/{GOKU}/tickets/", headers=visitor)
        assert response.status_code == 200
        assert [t["numero"] for t in response.json()] == ["DBZ-0001", "DBZ-0002", "DBZ-0006", "DBZ-0007"]

    async def test_a_visitor_cannot_read_someone_elses(
        self, client: AsyncClient, other_visitor: dict[str, str]
    ):
        response = await client.get(f"/user/{GOKU}/tickets/", headers=other_visitor)
        assert response.status_code == 400

    async def test_refuses_without_a_token(self, client: AsyncClient):
        response = await client.get(f"/user/{GOKU}/tickets/")
        assert response.status_code == 400


class TestCreateTicket:
    async def test_creates_a_ticket_for_the_caller(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        response = await client.post("/tickets/", json={"role": "Sayan"}, headers=visitor)
        assert response.status_code == 200
        assert response.json()["role"] == "sayan"

    async def test_refuses_a_role_that_does_not_exist(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        response = await client.post("/tickets/", json={}, headers=visitor)
        assert response.status_code == 400
        assert "role" in response.json()["detail"]

    async def test_refuses_without_a_token(self, client: AsyncClient):
        response = await client.post("/tickets/", json={"role": "sayan"})
        assert response.status_code == 400


class TestAssignTicket:
    async def test_claims_a_free_ticket(self, client: AsyncClient, visitor: dict[str, str]):
        response = await client.post(
            "/tickets/assign/", json={"numero": "DBZ-0003"}, headers=visitor
        )
        assert response.status_code == 200
        assert response.json()["numero"] == "DBZ-0003"

    async def test_unknown_and_taken_numbers_answer_the_same(
        self, client: AsyncClient, other_visitor: dict[str, str]
    ):
        unknown = await client.post(
            "/tickets/assign/", json={"numero": "DBZ-9999"}, headers=other_visitor
        )
        taken = await client.post(
            "/tickets/assign/", json={"numero": "DBZ-0001"}, headers=other_visitor
        )
        assert unknown.status_code == taken.status_code == 400
        # Otherwise the route tells you which numbers are real, and who holds them.
        assert unknown.json()["detail"] == taken.json()["detail"]

    async def test_refuses_a_body_without_a_number(
        self, client: AsyncClient, visitor: dict[str, str]
    ):
        response = await client.post("/tickets/assign/", json={}, headers=visitor)
        assert response.status_code == 400
        assert "numero" in response.json()["detail"]
