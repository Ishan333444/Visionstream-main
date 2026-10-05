import cv2
import numpy as np


class IntrusionDetector:
    """
    Detects when tracked people enter or exit an arbitrary polygon zone.
    """

    def __init__(self, polygon):

        # Example polygon (edit these points however you like)
        self.polygon = np.array(
            polygon,
            dtype=np.int32
        )

        self.inside_ids = set()

    def update(self, results):

        boxes = results[0].boxes

        current_inside = set()
        feet = []

        if boxes.id is None:

            self.inside_ids.clear()

            return {
                "inside": 0,
                "inside_ids": set(),
                "entered": [],
                "exited": [],
                "feet": feet
            }

        ids = boxes.id.cpu().numpy().astype(int)
        classes = boxes.cls.cpu().numpy().astype(int)
        xyxy = boxes.xyxy.cpu().numpy()

        for track_id, cls, box in zip(ids, classes, xyxy):

            # Only people
            if cls != 0:
                continue

            x1, y1, x2, y2 = box

            foot_x = int((x1 + x2) / 2)
            foot_y = int(y2)

            feet.append((foot_x, foot_y))

            inside = cv2.pointPolygonTest(
                self.polygon,
                (float(foot_x), float(foot_y)),
                False
            )

            if inside >= 0:
                current_inside.add(track_id)

        entered = current_inside - self.inside_ids
        exited = self.inside_ids - current_inside

        self.inside_ids = current_inside

        return {
            "inside": len(current_inside),
            "inside_ids": current_inside,
            "entered": list(entered),
            "exited": list(exited),
            "feet": feet
        }
