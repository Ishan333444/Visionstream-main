from pydantic import BaseModel


class StatsResponse(BaseModel):

    people: int

    entries: int

    exits: int

    intrusions: int

    density: str

    total_events: int
