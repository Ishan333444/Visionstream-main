import time

import cv2
import numpy as np


class IntrusionDetector:
    """Detect entries/exits from a polygon while tolerating brief missed tracks."""

    def __init__(self, polygon, missing_grace_seconds=1.0):
        self.polygon = np.array(polygon, dtype=np.int32)
        self.missing_grace_seconds = max(0.0, float(missing_grace_seconds))

        # IDs currently considered inside the zone.
        self.inside_ids = set()

        # track_id -> monotonic timestamp of its last observed foot point inside.
        # Retained briefly when the tracker misses that ID.
        self.last_seen_inside = {}

    def update(self, results):
        now = time.monotonic()
        boxes = results[0].boxes

        observed_person_ids = set()
        current_inside = set()
        feet = []

        # Ultralytics can return detections without track IDs (including a
        # frame with no detections). Do not interpret that alone as a zone exit.
        if boxes.id is not None:
            ids = boxes.id.cpu().numpy().astype(int)
            classes = boxes.cls.cpu().numpy().astype(int)
            xyxy = boxes.xyxy.cpu().numpy()

            for track_id, cls, box in zip(ids, classes, xyxy):
                # Only people (class 0 in the standard COCO class mapping).
                if cls != 0:
                    continue

                observed_person_ids.add(int(track_id))

                x1, y1, x2, y2 = box
                foot_x = int((x1 + x2) / 2)
                foot_y = int(y2)
                feet.append((foot_x, foot_y))

                inside = cv2.pointPolygonTest(
                    self.polygon,
                    (float(foot_x), float(foot_y)),
                    False,
                )

                if inside >= 0:
                    track_id = int(track_id)
                    current_inside.add(track_id)
                    self.last_seen_inside[track_id] = now

        # Preserve prior occupants only if their ID was not observed at all
        # and the last inside observation is still within the grace window.
        # If an ID is observed outside the polygon, it is treated as an exit.
        for track_id in self.inside_ids:
            if track_id in observed_person_ids:
                continue

            last_seen = self.last_seen_inside.get(track_id, now)
            if now - last_seen <= self.missing_grace_seconds:
                current_inside.add(track_id)

        entered = current_inside - self.inside_ids
        exited = self.inside_ids - current_inside
        self.inside_ids = current_inside

        # Keep timestamps only for current occupants / temporarily missing IDs.
        for track_id in list(self.last_seen_inside):
            if track_id not in self.inside_ids:
                del self.last_seen_inside[track_id]

        return {
            "inside": len(current_inside),
            "inside_ids": current_inside,
            "entered": list(entered),
            "exited": list(exited),
            "feet": feet,
        }
