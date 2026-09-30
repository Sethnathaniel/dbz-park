"""Attractions, and joining a queue."""

from datetime import datetime

from fastapi import APIRouter, Response
from sqlalchemy import exists, select

from app.config import get_settings
from app.db import SessionDep
from app.dependencies import CurrentUser
from app.errors import ALREADY_HERE, NO_FREE_TICKET, QUEUE_CLOSED, UNKNOWN_ATTRACTION, ApiError
from app.models import Attraction, AttractionVisit, QueueEntry, Ticket
from app.priority import fare_rank
from app.schemas.attractions import AttractionOut

router = APIRouter(prefix="/attractions", tags=["attractions"])


@router.get("/", response_model=list[AttractionOut])
async def list_attractions(user: CurrentUser, session: SessionDep) -> list[Attraction]:
    """The catalogue: the attractions themselves, and nothing about this visitor."""
    return list(await session.scalars(select(Attraction).order_by(Attraction.id)))


@router.post("/{attraction_id}/queue/join/")
async def join_queue(attraction_id: int, user: CurrentUser, session: SessionDep) -> Response:
    """Takes a place in the queue, with the visitor's best ticket not engaged anywhere."""
    if datetime.now().hour >= get_settings().queue_closing_hour:
        raise ApiError(QUEUE_CLOSED)

    if await session.get(Attraction, attraction_id) is None:
        raise ApiError(UNKNOWN_ATTRACTION)

    my_tickets = select(Ticket.id).where(Ticket.user_id == user.id)
    already_here = await session.scalar(
        select(
            exists().where(
                QueueEntry.attraction_id == attraction_id, QueueEntry.ticket_id.in_(my_tickets)
            )
            | exists().where(
                AttractionVisit.attraction_id == attraction_id,
                AttractionVisit.ticket_id.in_(my_tickets),
            )
        )
    )
    if already_here:
        raise ApiError(ALREADY_HERE)

    # A ticket holds one place or one visit at a time, wherever it is.
    ticket_id = await session.scalar(
        select(Ticket.id)
        .where(
            Ticket.user_id == user.id,
            Ticket.id.not_in(select(QueueEntry.ticket_id)),
            Ticket.id.not_in(select(AttractionVisit.ticket_id)),
        )
        .order_by(fare_rank(Ticket.role), Ticket.id)
        .limit(1)
    )
    if ticket_id is None:
        raise ApiError(NO_FREE_TICKET)

    session.add(QueueEntry(attraction_id=attraction_id, ticket_id=ticket_id, joined_at=datetime.now()))
    await session.commit()
    return Response(status_code=200)
