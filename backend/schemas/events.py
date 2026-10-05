from pydantic import BaseModel


class EventResponse(BaseModel):

    id: int

    event_type: str

    track_id: int

    source: str

    timestamp: str
