"""Who goes first in a queue: best fare first, then first come, first served.

One order, used in three places so they cannot disagree: who the worker calls, which
position a visitor is shown, and which of their tickets joining a queue spends.
"""

from sqlalchemy import case
from sqlalchemy.sql.elements import ColumnElement

# Super Saiyan, then Saiyan, then humans. The column is free text: any other role comes last.
FARE_ORDER = ["super_sayan", "sayan", "normal"]


def fare_rank(role: ColumnElement[str]) -> ColumnElement[int]:
    """The SQL rank of a role column, to sort ascending: 0 is served first."""
    return case(
        {fare: rank for rank, fare in enumerate(FARE_ORDER)}, value=role, else_=len(FARE_ORDER)
    )


def rank_of(role: str) -> int:
    """The same rank, for a role already read from the database."""
    return FARE_ORDER.index(role) if role in FARE_ORDER else len(FARE_ORDER)
