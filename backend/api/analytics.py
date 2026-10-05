from fastapi import APIRouter

from backend.schemas.analytics import AnalyticsResponse

router = APIRouter()

@router.get(
    "/analytics",
    response_model=AnalyticsResponse
)
def analytics():

    return get_latest()
