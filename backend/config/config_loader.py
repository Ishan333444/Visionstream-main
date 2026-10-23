"""Load, validate, normalize, and persist VisionStream calibration geometry."""
import json
import os
from pathlib import Path
import tempfile

CONFIG_PATH = Path(__file__).parent / "calibration.json"


def _point(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{label} must be a two-value [x, y] point")
    try:
        x, y = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} coordinates must be numbers") from exc
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
        raise ValueError(f"{label} coordinates must be normalized between 0 and 1")
    return [x, y]


def normalize_calibration(data):
    """Convert legacy single-line/single-zone data to the current multi-item schema."""
    if not isinstance(data, dict):
        raise ValueError("Calibration must be a JSON object")

    if "lines" in data:
        raw_lines = data.get("lines")
    elif isinstance(data.get("entry_line"), dict):
        raw_lines = [{"id": "line_1", "name": "Main counting line", **data["entry_line"]}]
    else:
        raw_lines = []

    if "zones" in data:
        raw_zones = data.get("zones")
    elif isinstance(data.get("intrusion_zone"), list):
        raw_zones = [{"id": "zone_1", "name": "Intrusion zone", "points": data["intrusion_zone"]}]
    else:
        raw_zones = []

    if not isinstance(raw_lines, list) or not raw_lines:
        raise ValueError("Configure at least one counting line")
    if not isinstance(raw_zones, list):
        raise ValueError("Zones must be a list")

    lines = []
    line_ids = set()
    for index, line in enumerate(raw_lines, 1):
        if not isinstance(line, dict):
            raise ValueError(f"Line {index} must be an object")
        line_id = str(line.get("id") or f"line_{index}").strip()
        name = str(line.get("name") or f"Counting line {index}").strip()
        if not line_id or line_id in line_ids:
            raise ValueError(f"Counting line IDs must be non-empty and unique: {line_id!r}")
        line_ids.add(line_id)
        start = _point(line.get("start"), f"Line '{name}' start")
        end = _point(line.get("end"), f"Line '{name}' end")
        if abs(start[0] - end[0]) < 1e-6 and abs(start[1] - end[1]) < 1e-6:
            raise ValueError(f"Line '{name}' start and end must be different")
        lines.append({"id": line_id, "name": name or line_id, "start": start, "end": end})

    zones = []
    zone_ids = set()
    for index, zone in enumerate(raw_zones, 1):
        if not isinstance(zone, dict):
            raise ValueError(f"Zone {index} must be an object")
        zone_id = str(zone.get("id") or f"zone_{index}").strip()
        name = str(zone.get("name") or f"Intrusion zone {index}").strip()
        if not zone_id or zone_id in zone_ids:
            raise ValueError(f"Zone IDs must be non-empty and unique: {zone_id!r}")
        zone_ids.add(zone_id)
        raw_points = zone.get("points", zone.get("polygon"))
        if not isinstance(raw_points, list) or len(raw_points) < 3:
            raise ValueError(f"Zone '{name}' must have at least three points")
        points = [_point(p, f"Zone '{name}' point {i}") for i, p in enumerate(raw_points, 1)]
        if len({(p[0], p[1]) for p in points}) < 3:
            raise ValueError(f"Zone '{name}' needs at least three distinct points")
        zones.append({"id": zone_id, "name": name or zone_id, "points": points})

    return {"lines": lines, "zones": zones}


def validate_calibration(data):
    return normalize_calibration(data)


def load_calibration(path=None):
    source = Path(path) if path else CONFIG_PATH
    with source.open("r", encoding="utf-8") as file:
        return normalize_calibration(json.load(file))


def save_calibration(data, path=None):
    """Validate and atomically write normalized calibration JSON."""
    normalized = normalize_calibration(data)
    destination = Path(path) if path else CONFIG_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent,
            prefix=destination.name + ".", suffix=".tmp", delete=False
        ) as temp_file:
            json.dump(normalized, temp_file, indent=2)
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_name = temp_file.name
        os.replace(temp_name, destination)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    return normalized


def scale_point(point, width, height):
    return int(round(point[0] * width)), int(round(point[1] * height))


def scale_polygon(points, width, height):
    return [scale_point(point, width, height) for point in points]
