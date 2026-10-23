import numpy as np

from backend.analytics.heatmaps import Heatmap


def test_repeated_visits_accumulate_activity():
    heatmap = Heatmap(width=40, height=40, radius=3)
    feet = [(20, 20)]

    heatmap.update(feet)
    first_peak = float(heatmap.map[20, 20])
    heatmap.update(feet)
    second_peak = float(heatmap.map[20, 20])

    assert first_peak == 1.0
    assert second_peak == 2.0


def test_empty_heatmap_does_not_tint_frame():
    heatmap = Heatmap(width=40, height=40, radius=3)
    frame = np.full((40, 40, 3), 127, dtype=np.uint8)

    result = heatmap.overlay(frame)

    assert np.array_equal(result, frame)
    assert result is not frame


def test_overlay_changes_active_pixels_but_not_unvisited_pixels():
    heatmap = Heatmap(width=40, height=40, radius=3)
    frame = np.full((40, 40, 3), 127, dtype=np.uint8)
    heatmap.update([(20, 20)])

    result = heatmap.overlay(frame, alpha=0.4)

    assert not np.array_equal(result[20, 20], frame[20, 20])
    assert np.array_equal(result[0, 0], frame[0, 0])
