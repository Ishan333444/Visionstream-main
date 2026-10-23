"""Run an independent crossing state machine for every configured counting line."""
from backend.analytics.line_counter import LineCounter
from backend.config.config_loader import scale_point
from backend.config.settings import Settings


class MultiLineCounter:
    def __init__(self, lines, width, height, previous=None):
        self.width = int(width)
        self.height = int(height)
        self.counters = {}
        self.names = {}
        self.retired_entries = 0
        self.retired_exits = 0
        if previous is not None:
            self.retired_entries = previous.retired_entries
            self.retired_exits = previous.retired_exits
        self.configure(lines, previous=previous)

    def configure(self, lines, previous=None):
        old = previous.counters if previous is not None else self.counters
        new_counters = {}
        new_names = {}
        for line in lines:
            line_id = line["id"]
            start = scale_point(line["start"], self.width, self.height)
            end = scale_point(line["end"], self.width, self.height)
            if line_id in old:
                old_counter = old[line_id]
                counter = LineCounter(
                    start, end,
                    margin=Settings.LINE_MARGIN,
                    confirm_frames=Settings.LINE_CONFIRM_FRAMES,
                    max_track_age_seconds=Settings.LINE_TRACK_STATE_MAX_AGE_SECONDS,
                )
                counter.entries = old_counter.entries
                counter.exits = old_counter.exits
            else:
                counter = LineCounter(
                    start, end,
                    margin=Settings.LINE_MARGIN,
                    confirm_frames=Settings.LINE_CONFIRM_FRAMES,
                    max_track_age_seconds=Settings.LINE_TRACK_STATE_MAX_AGE_SECONDS,
                )
            new_counters[line_id] = counter
            new_names[line_id] = line["name"]

        if previous is not None:
            for line_id, counter in previous.counters.items():
                if line_id not in new_counters:
                    self.retired_entries += counter.entries
                    self.retired_exits += counter.exits
        self.counters = new_counters
        self.names = new_names

    @property
    def entries(self):
        return self.retired_entries + sum(counter.entries for counter in self.counters.values())

    @property
    def exits(self):
        return self.retired_exits + sum(counter.exits for counter in self.counters.values())

    @property
    def lines(self):
        return [
            {"id": line_id, "name": self.names[line_id], "start": counter.start, "end": counter.end,
             "entries": counter.entries, "exits": counter.exits}
            for line_id, counter in self.counters.items()
        ]

    def reset_tracks(self):
        for counter in self.counters.values():
            counter.objects.clear()

    def update(self, results):
        per_line = []
        entered_ids = []
        exited_ids = []
        feet = []
        for line_id, counter in self.counters.items():
            result = counter.update(results)
            entered_ids.extend(result["entered_ids"])
            exited_ids.extend(result["exited_ids"])
            if not feet:
                feet = result["feet"]
            per_line.append({
                "id": line_id,
                "name": self.names[line_id],
                "entries": counter.entries,
                "exits": counter.exits,
                "entered_ids": result["entered_ids"],
                "exited_ids": result["exited_ids"],
            })
        return {
            "entries": self.entries,
            "exits": self.exits,
            "entered_ids": list(dict.fromkeys(entered_ids)),
            "exited_ids": list(dict.fromkeys(exited_ids)),
            "feet": feet,
            "per_line": per_line,
        }
