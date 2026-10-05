from typing import Dict

from pydantic import BaseModel


class AnalyticsResponse(BaseModel):

    people: int

    entries: int

    exits: int

    inside_zone: int

    density: str

    object_counts: Dict[str, int]

    updated_at: str
