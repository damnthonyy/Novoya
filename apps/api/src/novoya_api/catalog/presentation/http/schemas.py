from pydantic import BaseModel, ConfigDict


class DestinationResponse(BaseModel):
    """A place Novoya can plan a trip, from listed partner offers."""

    model_config = ConfigDict(frozen=True)

    country: str
    city: str
