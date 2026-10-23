from fastapi import APIRouter, HTTPException, Request

from backend.config.config_loader import load_calibration, normalize_calibration, save_calibration

router = APIRouter(prefix="/calibration", tags=["Calibration"])


@router.get("")
def get_calibration(request: Request):
    engine = getattr(request.app.state, "engine_instance", None)
    if engine is not None:
        return engine.get_calibration_status()
    try:
        return {"calibration": load_calibration(), "status": "engine_starting", "pending": False, "error": None}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not load calibration: {exc}") from exc


@router.put("")
def update_calibration(payload: dict, request: Request):
    try:
        normalized = normalize_calibration(payload)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    engine = getattr(request.app.state, "engine_instance", None)
    if engine is None:
        try:
            saved = save_calibration(normalized)
            return {"calibration": saved, "status": "saved_for_next_start", "pending": False, "error": None}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Could not save calibration: {exc}") from exc

    try:
        return engine.request_calibration_update(normalized)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
