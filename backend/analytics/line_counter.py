import math

class LineCounter:
    """
    Counts crossings over an arbitrary line segment using
    a finite state machine.

    The line is defined by two endpoints:

        start = (x1, y1)
        end   = (x2, y2)
    """

    def __init__(self, start, end, margin=20, confirm_frames=3):

        self.start = start
        self.end = end

        self.margin = margin
        self.confirm_frames = confirm_frames

        self.entries = 0
        self.exits = 0

        self.objects = {}

    def _get_side(self, point):

        ax, ay = self.start
        bx, by = self.end

        px, py = point

        cross = (
            (bx - ax) * (py - ay)
            - (by - ay) * (px - ax)
        )

        line_length = math.hypot(
            bx - ax,
            by - ay
        )

        if line_length == 0:
            return "middle"

        distance = cross / line_length

        if distance > self.margin:
            return "left"

        elif distance < -self.margin:
            return "right"

        return "middle"

    def update(self, results):

        boxes = results[0].boxes

        feet = []

        entered_ids = []
        exited_ids = []

        if boxes.id is None:
            return {
                "entries": self.entries,
                "exits": self.exits,
                "entered_ids": entered_ids,
                "exited_ids": exited_ids,
                "feet": feet,
            }

        ids = boxes.id.cpu().numpy().astype(int)
        classes = boxes.cls.cpu().numpy().astype(int)
        xyxy = boxes.xyxy.cpu().numpy()

        for track_id, cls, box in zip(ids, classes, xyxy):

            # Only track people
            if cls != 0:
                continue

            x1, y1, x2, y2 = box

            foot_x = (x1 + x2) / 2
            foot_y = y2

            feet.append((int(foot_x), int(foot_y)))

            side = self._get_side((foot_x, foot_y))

            if side == "middle":
                continue

            if track_id not in self.objects:

                self.objects[track_id] = {
                    "stable_side": side,
                    "candidate_side": None,
                    "candidate_frames": 0,
                }

                continue

            obj = self.objects[track_id]

            stable = obj["stable_side"]

            if side == stable:

                obj["candidate_side"] = None
                obj["candidate_frames"] = 0
                continue

            if obj["candidate_side"] != side:

                obj["candidate_side"] = side
                obj["candidate_frames"] = 1

            else:

                obj["candidate_frames"] += 1

            if obj["candidate_frames"] >= self.confirm_frames:

                if stable == "left" and side == "right":

                    self.entries += 1
                    entered_ids.append(track_id)

                elif stable == "right" and side == "left":

                    self.exits += 1
                    exited_ids.append(track_id)

                obj["stable_side"] = side
                obj["candidate_side"] = None
                obj["candidate_frames"] = 0

        return {
            "entries": self.entries,
            "exits": self.exits,
            "entered_ids": entered_ids,
            "exited_ids": exited_ids,
            "feet": feet,
        }
