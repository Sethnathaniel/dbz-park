from pydantic import BaseModel, ConfigDict


class AttractionOut(BaseModel):
    """An attraction, and nothing about the visitor asking."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    # No column yet: the front shows its default illustration for "".
    photo_url: str = ""
    max_people: int
    people_inside: int
    avg_duration: int


class PositionOut(BaseModel):
    """Waiting places ahead, this one included: 1 = next in line, 0 = already called."""

    position: int
