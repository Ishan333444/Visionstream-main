import time


class DwellTimer:
    """
    Tracks how long each object remains inside the intrusion zone.
    """

    def __init__(self):

        # track_id -> entry timestamp
        self.entry_times = {}

    def update(self, inside_ids):

        now = time.time()

        # -------------------------
        # Register new entries
        # -------------------------
        for track_id in inside_ids:

            if track_id not in self.entry_times:
                self.entry_times[track_id] = now

        # -------------------------
        # Remove exited objects
        # -------------------------
        for track_id in list(self.entry_times.keys()):

            if track_id not in inside_ids:
                del self.entry_times[track_id]

        # -------------------------
        # Compute dwell times
        # -------------------------
        dwell_times = {}

        for track_id, start_time in self.entry_times.items():

            dwell_times[track_id] = now - start_time

        return dwell_times
