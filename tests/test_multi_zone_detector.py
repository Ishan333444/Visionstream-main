from types import SimpleNamespace
import numpy as np
from backend.analytics.multi_zone_detector import MultiZoneDetector


class FakeTensor:
    def __init__(self, values): self.values = values
    def cpu(self): return self
    def numpy(self): return np.asarray(self.values)


def result(track_id, x, y):
    boxes = SimpleNamespace(id=FakeTensor([track_id]), cls=FakeTensor([0]), xyxy=FakeTensor([[x-3, y-10, x+3, y]]))
    return [SimpleNamespace(boxes=boxes)]


def test_multiple_zones_report_per_zone_and_unique_overall_occupancy():
    zones = [
        {"id": "a", "name": "A", "points": [[0.0, 0.0], [0.6, 0.0], [0.6, 1.0], [0.0, 1.0]]},
        {"id": "b", "name": "B", "points": [[0.4, 0.0], [1.0, 0.0], [1.0, 1.0], [0.4, 1.0]]},
    ]
    detector = MultiZoneDetector(zones, width=100, height=100)
    result_data = detector.update(result(1, 50, 50))
    assert result_data["inside"] == 1
    assert len(result_data["per_zone"]) == 2
    assert [zone["inside"] for zone in result_data["per_zone"]] == [1, 1]
