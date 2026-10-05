from fastapi import APIRouter, Request

from backend.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse
)
def health(request: Request):

    engine_status = getattr(
        request.app.state,
        "engine_status",
        "unknown"
    )

    status = (
        "healthy"
        if engine_status == "running"
        else "degraded"
    )

    return {
        "status": status
    }