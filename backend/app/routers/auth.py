"""Accounts. These three routes are written: everything else depends on them.

There is no logout route: the token is a signed JWT the back cannot revoke, so logging
out means the front dropping its own token.
"""

from fastapi import APIRouter
from sqlalchemy import select

from app.db import SessionDep
from app.dependencies import CurrentUser
from app.errors import USERNAME_TAKEN, ApiError
from app.models import User
from app.schemas.auth import AuthOut, LoginIn, SignupIn, UserOut
from app.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup/", response_model=AuthOut)
async def signup(data: SignupIn, session: SessionDep) -> AuthOut:
    if data.password1 != data.password2:
        raise ApiError("Les deux mots de passe ne sont pas identiques.")

    taken = await session.scalar(select(User).where(User.username == data.username))
    if taken is not None:
        raise ApiError(USERNAME_TAKEN)

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password1),
        is_staff=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return AuthOut(token=create_token(user.id), user=UserOut.model_validate(user))


@router.post("/login/", response_model=AuthOut)
async def login(data: LoginIn, session: SessionDep) -> AuthOut:
    user = await session.scalar(select(User).where(User.username == data.username))

    # One message for both cases: the answer must never confirm that an account exists.
    if user is None or not verify_password(data.password, user.password_hash):
        raise ApiError("Nom d'utilisateur ou mot de passe incorrect.")

    return AuthOut(token=create_token(user.id), user=UserOut.model_validate(user))


@router.get("/me/", response_model=UserOut)
async def me(user: CurrentUser) -> User:
    """Who is logged in, per the token. A 400 here tells the front to drop it."""
    return user
