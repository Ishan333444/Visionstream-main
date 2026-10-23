from types import SimpleNamespace

import numpy as np

from backend.analytics.line_counter import LineCounter


class FakeTensor:
    def __init__(self, values):
        self.values = values

    def cpu(self):
        return self

    def numpy(self):
        return np.asarray(self.values)


def make_results(track_id, foot_x, foot_y, *, cls=0):
    # Make a box whose bottom-center is the requested foot point.
    boxes = SimpleNamespace(
        id=FakeTensor([track_id]),
        cls=FakeTensor([cls]),
        xyxy=FakeTensor([[foot_x - 5, foot_y - 20, foot_x + 5, foot_y]]),
    )
    return [SimpleNamespace(boxes=boxes)]


def test_crossing_inside_finite_segment_is_counted_after_confirmation():
    counter = LineCounter(start=(0, 50), end=(100, 50), margin=2, confirm_frames=2)
    counter.update(make_results(1, 50, 40))  # establish left side
    counter.update(make_results(1, 50, 60))  # cross the configured segment
    result = counter.update(make_results(1, 50, 62))  # confirm new side

    assert result["exits"] == 1
    assert result["exited_ids"] == [1]


def test_crossing_in_infinite_line_extension_is_not_counted():
    counter = LineCounter(start=(0, 50), end=(100, 50), margin=2, confirm_frames=2)
    counter.update(make_results(2, 150, 40))  # beyond the right endpoint
    counter.update(make_results(2, 150, 60))  # crosses only the line's extension
    result = counter.update(make_results(2, 150, 62))

    assert result["entries"] == 0
    assert result["exits"] == 0
    assert result["entered_ids"] == []
    assert result["exited_ids"] == []


def test_crossing_extension_then_moving_onto_other_side_does_not_count_later():
    counter = LineCounter(start=(0, 50), end=(100, 50), margin=2, confirm_frames=2)
    counter.update(make_results(3, 150, 40))
    counter.update(make_results(3, 150, 60))
    counter.update(make_results(3, 150, 62))  # settles on right side without count
    counter.update(make_results(3, 50, 62))   # move along the right side
    result = counter.update(make_results(3, 50, 40))
    result = counter.update(make_results(3, 50, 38))

    assert result["entries"] == 1  # this later crossing really intersects the segment
    assert result["exits"] == 0


def test_non_person_classes_are_ignored():
    counter = LineCounter(start=(0, 50), end=(100, 50), margin=2, confirm_frames=2)
    counter.update(make_results(4, 50, 40, cls=2))
    result = counter.update(make_results(4, 50, 60, cls=2))

    assert result["entries"] == 0
    assert result["exits"] == 0


def make_empty_results():
    boxes = SimpleNamespace(id=None, cls=None, xyxy=None)
    return [SimpleNamespace(boxes=boxes)]


def test_stale_track_state_is_pruned_after_configured_timeout():
    counter = LineCounter(
        start=(0, 50), end=(100, 50), margin=2,
        confirm_frames=2, max_track_age_seconds=10,
    )
    counter.update(make_results(9, 50, 40))
    counter.objects[9]["last_seen_at"] -= 11

    # Pruning must still happen when the detector has no IDs this frame.
    counter.update(make_empty_results())

    assert 9 not in counter.objects


def test_recently_missing_track_state_is_retained():
    counter = LineCounter(
        start=(0, 50), end=(100, 50), margin=2,
        confirm_frames=2, max_track_age_seconds=10,
    )
    counter.update(make_results(10, 50, 40))
    counter.objects[10]["last_seen_at"] -= 5

    counter.update(make_empty_results())

    assert 10 in counter.objects


def test_seen_track_refreshes_last_seen_timestamp():
    counter = LineCounter(
        start=(0, 50), end=(100, 50), margin=2,
        confirm_frames=2, max_track_age_seconds=10,
    )
    counter.update(make_results(11, 50, 40))
    old_timestamp = counter.objects[11]["last_seen_at"]
    counter.update(make_results(11, 50, 40))

    assert counter.objects[11]["last_seen_at"] >= old_timestamp


def test_middle_observation_resets_consecutive_confirmation_streak():
    counter = LineCounter(start=(0, 50), end=(100, 50), margin=2, confirm_frames=3)
    counter.update(make_results(20, 50, 40))  # stable side
    counter.update(make_results(20, 50, 60))  # candidate frame 1
    counter.update(make_results(20, 50, 60))  # candidate frame 2
    counter.update(make_results(20, 50, 50))  # middle breaks the streak
    result = counter.update(make_results(20, 50, 60))  # candidate frame 1 again
    assert result["entries"] + result["exits"] == 0
    result = counter.update(make_results(20, 50, 60))  # candidate frame 2 again
    assert result["entries"] + result["exits"] == 0
    result = counter.update(make_results(20, 50, 60))  # candidate frame 3
    assert result["entries"] + result["exits"] == 1
