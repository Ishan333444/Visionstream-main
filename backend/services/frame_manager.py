import threading

_latest_frame = None
_lock = threading.Lock()


def set_frame(frame):
    global _latest_frame

    with _lock:
        _latest_frame = frame.copy()


def get_frame():
    with _lock:
        if _latest_frame is None:
            return None

        return _latest_frame.copy()
