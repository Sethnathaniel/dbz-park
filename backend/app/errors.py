"""The contract allows two answers only: `200` and `400`.

Every refusal goes through `ApiError`, which produces the `{"detail": "..."}` body the
front prints as is. That message is the only information sent, so it must tell the
visitor what to do and never reveal what they are not entitled to know.
"""

from fastapi import HTTPException

# Messages shared by several routes: one place to check nothing leaks.
NOT_AUTHENTICATED = "Connectez-vous pour accéder à cette page."
NOT_STAFF = NOT_AUTHENTICATED  # deliberately identical
UNKNOWN_TICKET = "Ce billet est introuvable."
UNKNOWN_USER = "Ces billets sont introuvables."
UNKNOWN_ENTRY = "Cette place est introuvable."
UNKNOWN_ATTRACTION = "Cette attraction est introuvable."
UNKNOWN_ACCOUNT = "Ce compte est introuvable."
USERNAME_TAKEN = "Ce nom d'utilisateur est déjà pris."
ALREADY_HERE = "Vous avez déjà une place ou êtes déjà dans cette attraction."
NO_FREE_TICKET = "Aucun de vos billets n'est disponible."
QUEUE_CLOSED = "Les files d'attente sont fermées pour aujourd'hui."
NOT_CALLED = "Ce n'est pas encore votre tour."
TURN_MISSED = "Votre tour est passé."
ATTRACTION_FULL = "L'attraction est pleine, il faut attendre une sortie."
OUT_OF_SERVICE = "L'attraction est hors service : la file reprendra à sa réouverture."


class ApiError(HTTPException):
    """The only error of the project: `raise ApiError("…")` → 400 + detail."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=400, detail=detail)

