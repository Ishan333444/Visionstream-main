from typing import List
from typing import Optional

from fastapi import APIRouter

from backend.schemas.events import EventResponse
from backend.services.event_repository import get_events

router = APIRouter()


@router.get(
    "/events",
    response_model=List[EventResponse]
)
def events(
    limit: Optional[int] = None,
    event_type: Optional[str] = None,
):

    return get_events(
        limit=limit,
        event_type=event_type
    )
