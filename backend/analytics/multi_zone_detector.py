"""Combine multiple independently tracked intrusion polygons."""
from backend.analytics.intrusion_detector import IntrusionDetector
from backend.config.config_loader import scale_polygon
from backend.config.settings import Settings


class MultiZoneDetector:
    def __init__(self, zones, width, height):
        self.width = int(width)
        self.height = int(height)
        self.detectors = {}
        self.names = {}
        self.configure(zones)

    def configure(self, zones):
        self.detectors = {}
        self.names = {}
        for zone in zones:
            self.detectors[zone["id"]] = IntrusionDetector(
                scale_polygon(zone["points"], self.width, self.height),
                missing_grace_seconds=Settings.INTRUSION_MISSING_GRACE_SECONDS,
            )
            self.names[zone["id"]] = zone["name"]

    @property
    def inside_ids(self):
        result = set()
        for detector in self.detectors.values():
            result.update(detector.inside_ids)
        return result

    @property
    def polygons(self):
        return [
            {"id": zone_id, "name": self.names[zone_id], "polygon": detector.polygon,
             "inside": len(detector.inside_ids)}
            for zone_id, detector in self.detectors.items()
        ]

    def reset_tracking(self):
        for detector in self.detectors.values():
            detector.inside_ids.clear()
            detector.last_seen_inside.clear()

    def update(self, results):
        previous_inside = self.inside_ids
        per_zone = []
        current_inside = set()
        feet = []
        for zone_id, detector in self.detectors.items():
            result = detector.update(results)
            current_inside.update(result["inside_ids"])
            if not feet:
                feet = result["feet"]
            per_zone.append({"id": zone_id, "name": self.names[zone_id], "inside": result["inside"]})
        return {
            "inside": len(current_inside),
            "inside_ids": current_inside,
            "entered": list(current_inside - previous_inside),
            "exited": list(previous_inside - current_inside),
            "feet": feet,
            "per_zone": per_zone,
        }
