"""A visitor, or a staff member (`is_staff`)."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class User(Base):
    # "user" is a Postgres reserved word: SQLAlchemy quotes it, handwritten SQL must too.
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    # `unique=True` alone: Postgres already indexes a unique constraint.
    username: Mapped[str] = mapped_column(String(150), unique=True)

    # Three fields the contract needs but the given schema does not carry.
    email: Mapped[str] = mapped_column(String(254), default="")
    password_hash: Mapped[str] = mapped_column(String(128))
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="user", order_by="Ticket.id")

    def __repr__(self) -> str:
        return f"<User {self.username}>"
