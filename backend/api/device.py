from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.detector.yolo_detector import describe_device

router = APIRouter(prefix="/device", tags=["Device"] )


class DeviceChangeRequest(BaseModel):
    device: Literal["auto", "cpu", "cuda"]


@router.get("")
def get_device(request: Request):
    engine = getattr(request.app.state, "engine_instance", None)
    if engine is None:
        return {
            **describe_device(),
            "status": "starting",
            "pending_setting": None,
            "error": None,
            "supported_settings": ["auto", "cpu", "cuda"],
        }
    try:
        return engine.get_device_status()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("")
def set_device(payload: DeviceChangeRequest, request: Request):
    engine = getattr(request.app.state, "engine_instance", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="VisionStream engine is not ready")
    try:
        return engine.request_device_change(payload.device)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
