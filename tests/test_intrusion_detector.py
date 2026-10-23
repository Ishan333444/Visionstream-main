from types import SimpleNamespace

import numpy as np

from backend.analytics import intrusion_detector as intrusion_module
from backend.analytics.intrusion_detector import IntrusionDetector


class FakeTensor:
    def __init__(self, values):
        self.values = values

    def cpu(self):
        return self

    def numpy(self):
        return np.asarray(self.values)


def make_results(detections=None, ids_available=True):
    """detections: tuples of (track_id, class_id, [x1, y1, x2, y2])."""
    detections = detections or []
    if not ids_available:
        boxes = SimpleNamespace(id=None, cls=FakeTensor([]), xyxy=FakeTensor([]))
    else:
        boxes = SimpleNamespace(
            id=FakeTensor([d[0] for d in detections]),
            cls=FakeTensor([d[1] for d in detections]),
            xyxy=FakeTensor([d[2] for d in detections]),
        )
    return [SimpleNamespace(boxes=boxes)]


def test_missing_ids_preserve_occupancy_then_expire(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(intrusion_module.time, "monotonic", lambda: now[0])
    detector = IntrusionDetector(
        polygon=[(0, 0), (100, 0), (100, 100), (0, 100)],
        missing_grace_seconds=1.0,
    )

    first = detector.update(make_results([(7, 0, [40, 10, 60, 50])]))
    assert first["inside_ids"] == {7}
    assert first["entered"] == [7]
    assert first["exited"] == []

    now[0] += 0.4
    missing = detector.update(make_results(ids_available=False))
    assert missing["inside_ids"] == {7}
    assert missing["inside"] == 1
    assert missing["entered"] == []
    assert missing["exited"] == []

    now[0] += 1.1
    expired = detector.update(make_results(ids_available=False))
    assert expired["inside_ids"] == set()
    assert expired["inside"] == 0
    assert expired["exited"] == [7]


def test_observed_person_outside_zone_exits_immediately(monkeypatch):
    now = [200.0]
    monkeypatch.setattr(intrusion_module.time, "monotonic", lambda: now[0])
    detector = IntrusionDetector(
        polygon=[(0, 0), (100, 0), (100, 100), (0, 100)],
        missing_grace_seconds=1.0,
    )

    detector.update(make_results([(7, 0, [40, 10, 60, 50])]))
    result = detector.update(make_results([(7, 0, [40, 100, 60, 150])]))
    assert result["inside_ids"] == set()
    assert result["exited"] == [7]


def test_other_classes_do_not_enter_intrusion_zone(monkeypatch):
    monkeypatch.setattr(intrusion_module.time, "monotonic", lambda: 300.0)
    detector = IntrusionDetector(
        polygon=[(0, 0), (100, 0), (100, 100), (0, 100)],
    )
    result = detector.update(make_results([(42, 2, [40, 10, 60, 50])]))
    assert result["inside_ids"] == set()
    assert result["entered"] == []


def test_same_id_returning_within_grace_is_not_a_new_entry(monkeypatch):
    now = [400.0]
    monkeypatch.setattr(intrusion_module.time, "monotonic", lambda: now[0])
    detector = IntrusionDetector(
        polygon=[(0, 0), (100, 0), (100, 100), (0, 100)],
        missing_grace_seconds=1.0,
    )

    detector.update(make_results([(7, 0, [40, 10, 60, 50])]))
    now[0] += 0.3
    detector.update(make_results(ids_available=False))
    now[0] += 0.3
    returned = detector.update(make_results([(7, 0, [42, 10, 62, 50])]))

    assert returned["inside_ids"] == {7}
    assert returned["entered"] == []
    assert returned["exited"] == []
