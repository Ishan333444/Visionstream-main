import math
import time

class LineCounter:
    """
    Counts crossings over an arbitrary line segment using
    a finite state machine.

    The line is defined by two endpoints:

        start = (x1, y1)
        end   = (x2, y2)
    """

    def __init__(self, start, end, margin=20, confirm_frames=3, max_track_age_seconds=30.0):

        self.start = start
        self.end = end

        self.margin = margin
        self.confirm_frames = confirm_frames
        self.max_track_age_seconds = max(0.0, float(max_track_age_seconds))

        self.entries = 0
        self.exits = 0

        self.objects = {}

    def _prune_stale_tracks(self, now):
        """Forget per-track crossing state after a prolonged detection gap."""
        stale_ids = [
            track_id
            for track_id, state in self.objects.items()
            if now - state.get("last_seen_at", now) > self.max_track_age_seconds
        ]
        for track_id in stale_ids:
            del self.objects[track_id]

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

    def _crosses_finite_segment(self, previous, current):
        """Return whether the movement segment intersects the configured line segment."""
        if previous is None:
            return False

        px, py = previous
        qx, qy = current
        ax, ay = self.start
        bx, by = self.end

        # Movement vector r and counting-line vector s.
        rx, ry = qx - px, qy - py
        sx, sy = bx - ax, by - ay
        denominator = rx * sy - ry * sx
        if abs(denominator) < 1e-9:
            # Parallel or collinear movement is not a clear crossing.
            return False

        apx, apy = ax - px, ay - py
        t = (apx * sy - apy * sx) / denominator
        u = (apx * ry - apy * rx) / denominator

        # t locates the intersection on the person's movement segment;
        # u locates it on the configured counting segment.
        epsilon = 1e-9
        return -epsilon <= t <= 1 + epsilon and -epsilon <= u <= 1 + epsilon

    def update(self, results):

        now = time.monotonic()
        self._prune_stale_tracks(now)

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

            point = (foot_x, foot_y)
            side = self._get_side(point)

            if side == "middle":
                # Ambiguous observations break a consecutive confirmation streak,
                # but do not change the last confirmed side of the track.
                if track_id in self.objects:
                    self.objects[track_id]["candidate_side"] = None
                    self.objects[track_id]["candidate_frames"] = 0
                    self.objects[track_id]["candidate_crossed_segment"] = False
                    self.objects[track_id]["last_point"] = point
                    self.objects[track_id]["last_seen_at"] = now
                continue

            if track_id not in self.objects:

                self.objects[track_id] = {
                    "stable_side": side,
                    "candidate_side": None,
                    "candidate_frames": 0,
                    "last_point": (foot_x, foot_y),
                    "candidate_crossed_segment": False,
                    "last_seen_at": now,
                }

                continue

            obj = self.objects[track_id]
            obj["last_seen_at"] = now
            previous_point = obj.get("last_point")
            stable = obj["stable_side"]

            if side == stable:
                obj["candidate_side"] = None
                obj["candidate_frames"] = 0
                obj["candidate_crossed_segment"] = False
                obj["last_point"] = point
                continue

            if obj["candidate_side"] != side:
                obj["candidate_side"] = side
                obj["candidate_frames"] = 1
                obj["candidate_crossed_segment"] = self._crosses_finite_segment(
                    previous_point, point
                )
            else:
                obj["candidate_frames"] += 1

            obj["last_point"] = point

            if obj["candidate_frames"] >= self.confirm_frames:
                # Confirm the side change either way, but only count it when
                # the observed movement crossed the finite configured segment.
                if obj["candidate_crossed_segment"]:
                    if stable == "left" and side == "right":
                        self.entries += 1
                        entered_ids.append(track_id)
                    elif stable == "right" and side == "left":
                        self.exits += 1
                        exited_ids.append(track_id)

                obj["stable_side"] = side
                obj["candidate_side"] = None
                obj["candidate_frames"] = 0
                obj["candidate_crossed_segment"] = False

        return {
            "entries": self.entries,
            "exits": self.exits,
            "entered_ids": entered_ids,
            "exited_ids": exited_ids,
            "feet": feet,
        }
