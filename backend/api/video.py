import cv2
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from fastapi import HTTPException

from backend.services.frame_manager import get_frame

router = APIRouter(tags=["Video"])


def generate_frames():
    while True:

        frame = get_frame()

        if frame is None:
            time.sleep(0.03)
            continue

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )


@router.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/snapshot")
def snapshot():
    """Return the latest processed frame as a JPEG for calibration preview."""
    frame = get_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="No camera frame is available yet")
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        raise HTTPException(status_code=500, detail="Could not encode camera snapshot")
    return Response(content=buffer.tobytes(), media_type="image/jpeg")
