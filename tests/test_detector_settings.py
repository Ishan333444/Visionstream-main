import sys
import types

# Keep these unit tests independent of heavyweight runtime packages.
# The tests exercise argument forwarding, not model inference or GPU selection.
if "ultralytics" not in sys.modules:
    ultralytics_stub = types.ModuleType("ultralytics")
    ultralytics_stub.YOLO = object
    sys.modules["ultralytics"] = ultralytics_stub
if "torch" not in sys.modules:
    torch_stub = types.ModuleType("torch")
    torch_stub.cuda = types.SimpleNamespace(is_available=lambda: False)
    sys.modules["torch"] = torch_stub

from backend.config.settings import Settings
from backend.detector.yolo_detector import YOLODetector


class FakeModel:
    def __init__(self):
        self.call_args = None
        self.track_args = None

    def __call__(self, frame, **kwargs):
        self.call_args = (frame, kwargs)
        return "detections"

    def track(self, frame, **kwargs):
        self.track_args = (frame, kwargs)
        return "tracks"


def make_detector():
    detector = YOLODetector.__new__(YOLODetector)
    detector.device = "cpu"
    detector.model = FakeModel()
    return detector


def test_detect_passes_configured_confidence_and_iou():
    detector = make_detector()
    frame = object()

    result = detector.detect(frame)

    assert result == "detections"
    passed_frame, kwargs = detector.model.call_args
    assert passed_frame is frame
    assert kwargs["conf"] == Settings.DETECTION_CONFIDENCE
    assert kwargs["iou"] == Settings.DETECTION_IOU
    assert kwargs["device"] == "cpu"
    assert kwargs["verbose"] is False


def test_track_passes_configured_confidence_and_iou_and_preserves_tracker_options():
    detector = make_detector()
    frame = object()

    result = detector.track(frame)

    assert result == "tracks"
    passed_frame, kwargs = detector.model.track_args
    assert passed_frame is frame
    assert kwargs["conf"] == Settings.DETECTION_CONFIDENCE
    assert kwargs["iou"] == Settings.DETECTION_IOU
    assert kwargs["persist"] is True
    assert kwargs["tracker"] == "bytetrack.yaml"
    assert kwargs["device"] == "cpu"
    assert kwargs["verbose"] is False
