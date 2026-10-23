import cv2
import time


def open_capture_with_retries(
    source,
    max_attempts,
    initial_delay,
    max_delay,
    capture_factory=None,
    sleep_fn=None,
):
    """Open a video source and read its first frame, retrying with backoff.

    Returns (capture, first_frame). The caller owns the returned capture and
    must release it. Failed captures are released before the next attempt.
    """
    capture_factory = capture_factory or cv2.VideoCapture
    sleep_fn = sleep_fn or time.sleep
    delay = max(0.0, float(initial_delay))
    max_delay = max(0.0, float(max_delay))
    last_error = "source could not be opened or did not return a frame"

    for attempt in range(1, max(1, int(max_attempts)) + 1):
        cap = capture_factory(source)
        try:
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    return cap, frame
                last_error = "source opened but failed to provide an initial frame"
            else:
                last_error = "source could not be opened"
        except Exception as exc:
            last_error = str(exc)

        cap.release()
        if attempt < max(1, int(max_attempts)):
            sleep_fn(delay)
            delay = min(max_delay, max(delay * 2, 0.1))

    raise RuntimeError(
        f"Could not open camera/video source after {max(1, int(max_attempts))} attempts: {last_error}"
    )



def is_live_source(source):
    """Treat camera indexes and common network-stream URLs as live sources."""
    if isinstance(source, int):
        return True
    if isinstance(source, str):
        return source.lower().startswith(("rtsp://", "rtmp://", "http://", "https://"))
    return False
