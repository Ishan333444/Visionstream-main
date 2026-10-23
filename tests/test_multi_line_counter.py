from types import SimpleNamespace
import numpy as np
from backend.analytics.multi_line_counter import MultiLineCounter


class FakeTensor:
    def __init__(self, values): self.values = values
    def cpu(self): return self
    def numpy(self): return np.asarray(self.values)


def result(track_id, x, y):
    boxes = SimpleNamespace(id=FakeTensor([track_id]), cls=FakeTensor([0]), xyxy=FakeTensor([[x-3, y-10, x+3, y]]))
    return [SimpleNamespace(boxes=boxes)]


def test_multiple_lines_count_independently():
    lines = [
        {"id": "a", "name": "A", "start": [0.0, 0.25], "end": [1.0, 0.25]},
        {"id": "b", "name": "B", "start": [0.0, 0.75], "end": [1.0, 0.75]},
    ]
    counter = MultiLineCounter(lines, width=100, height=200)
    counter.update(result(1, 50, 10))
    counter.update(result(1, 50, 190))
    counter.update(result(1, 50, 195))
    counter.update(result(1, 50, 195))
    assert counter.entries + counter.exits >= 2
    assert len(counter.lines) == 2
    per_line = counter.update(result(1, 50, 195))["per_line"]
    assert len(per_line) == 2
    assert sum(item["entries"] + item["exits"] for item in per_line) >= 2


def test_removed_line_totals_are_not_lost_during_reconfiguration():
    lines = [
        {"id": "a", "name": "A", "start": [0.0, 0.5], "end": [1.0, 0.5]},
        {"id": "b", "name": "B", "start": [0.0, 0.8], "end": [1.0, 0.8]},
    ]
    first = MultiLineCounter(lines, width=100, height=100)
    first.counters["b"].entries = 3
    updated = MultiLineCounter([lines[0]], width=100, height=100, previous=first)
    assert updated.entries == first.entries
    assert len(updated.lines) == 1
