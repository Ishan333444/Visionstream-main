import json
import pytest

from backend.config.config_loader import load_calibration, normalize_calibration, save_calibration


def legacy_calibration():
    return {
        "entry_line": {"start": [0.1, 0.2], "end": [0.8, 0.2]},
        "intrusion_zone": [[0.1, 0.4], [0.5, 0.4], [0.5, 0.9], [0.1, 0.9]],
    }


def test_legacy_calibration_migrates_to_multi_item_schema():
    result = normalize_calibration(legacy_calibration())
    assert len(result["lines"]) == 1
    assert result["lines"][0]["id"] == "line_1"
    assert len(result["zones"]) == 1
    assert result["zones"][0]["id"] == "zone_1"


def test_multiple_lines_and_zones_are_preserved():
    payload = {
        "lines": [
            {"id": "front", "name": "Front", "start": [0.1, 0.2], "end": [0.8, 0.2]},
            {"id": "back", "name": "Back", "start": [0.2, 0.7], "end": [0.9, 0.7]},
        ],
        "zones": [
            {"id": "restricted", "name": "Restricted", "points": [[0.1, 0.1], [0.3, 0.1], [0.3, 0.3]]},
            {"id": "storage", "name": "Storage", "points": [[0.6, 0.6], [0.9, 0.6], [0.9, 0.9]]},
        ],
    }
    result = normalize_calibration(payload)
    assert [item["id"] for item in result["lines"]] == ["front", "back"]
    assert [item["id"] for item in result["zones"]] == ["restricted", "storage"]


def test_at_least_one_line_is_required():
    with pytest.raises(ValueError, match="at least one counting line"):
        normalize_calibration({"lines": [], "zones": []})


def test_line_endpoints_must_be_different():
    with pytest.raises(ValueError, match="must be different"):
        normalize_calibration({"lines": [{"id": "l", "start": [0.2, 0.2], "end": [0.2, 0.2]}], "zones": []})


def test_zone_needs_three_points():
    with pytest.raises(ValueError, match="at least three points"):
        normalize_calibration({"lines": [{"id": "l", "start": [0.1, 0.1], "end": [0.9, 0.9]}], "zones": [{"id": "z", "points": [[0.1, 0.1], [0.9, 0.9]]}]})


def test_coordinates_must_be_normalized():
    with pytest.raises(ValueError, match="between 0 and 1"):
        normalize_calibration({"lines": [{"id": "l", "start": [-0.1, 0.1], "end": [0.9, 0.9]}], "zones": []})


def test_calibration_save_and_reload(tmp_path):
    path = tmp_path / "calibration.json"
    payload = normalize_calibration(legacy_calibration())
    save_calibration(payload, path=path)
    assert load_calibration(path=path) == payload
    assert json.loads(path.read_text()) == payload
