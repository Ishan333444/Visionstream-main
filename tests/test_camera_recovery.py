from types import SimpleNamespace

import numpy as np
import pytest

from backend.engine.camera_recovery import is_live_source, open_capture_with_retries


class FakeCapture:
    def __init__(self, opened=True, frame_ok=True):
        self.opened = opened
        self.frame_ok = frame_ok
        self.released = False
        self.frame = np.zeros((2, 2, 3), dtype=np.uint8)

    def isOpened(self):
        return self.opened

    def read(self):
        return self.frame_ok, self.frame if self.frame_ok else None

    def release(self):
        self.released = True


def test_open_capture_retries_after_failed_open_and_returns_first_frame():
    captures = [FakeCapture(opened=False), FakeCapture(frame_ok=True)]
    delays = []

    cap, frame = open_capture_with_retries(
        source=0,
        max_attempts=2,
        initial_delay=0.25,
        max_delay=1.0,
        capture_factory=lambda _source: captures.pop(0),
        sleep_fn=delays.append,
    )

    assert cap.frame_ok is True
    assert frame.shape == (2, 2, 3)
    assert len(delays) == 1
    assert delays[0] == 0.25


def test_open_capture_releases_failed_handles_and_stops_after_limit():
    captures = [FakeCapture(opened=False), FakeCapture(frame_ok=False)]
    delays = []

    with pytest.raises(RuntimeError, match="after 2 attempts"):
        open_capture_with_retries(
            source=0,
            max_attempts=2,
            initial_delay=0.2,
            max_delay=1.0,
            capture_factory=lambda _source: captures.pop(0),
            sleep_fn=delays.append,
        )

    # Both failed capture handles were released before returning the error.
    assert len(captures) == 0
    assert delays == [0.2]


def test_live_source_detection_distinguishes_files_from_streams():
    assert is_live_source(0) is True
    assert is_live_source("rtsp://camera/stream") is True
    assert is_live_source("clip.mp4") is False

