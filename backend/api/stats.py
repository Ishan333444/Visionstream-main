from fastapi import APIRouter

from backend.schemas.stats import StatsResponse

from backend.services.analytics_repository import get_latest
from backend.services.event_repository import get_total_events

router = APIRouter()


@router.get(
    "/stats",
    response_model=StatsResponse
)
def stats():

    analytics = get_latest()

    total_events = get_total_events()

    return {
        "people": analytics["people"],
        "entries": analytics["entries"],
        "exits": analytics["exits"],
        "intrusions": analytics["inside_zone"],
        "density": analytics["density"],
        "total_events": total_events,
    }
