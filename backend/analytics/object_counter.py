from collections import defaultdict


class ObjectCounter:
    """
    Counts every detected object class.

    Returns:
    {
        "counts": {
            "person": 2,
            "chair": 1,
            "cell phone": 1,
            "laptop": 1
        },

        "track_ids": {
            "person": [3, 7],
            "chair": [5],
            "cell phone": [9],
            "laptop": [12]
        }
    }
    """

    def __init__(self, class_names):

        self.class_names = class_names

    def count(self, results):

        boxes = results[0].boxes

        if boxes.cls is None:
            return {
                "counts": {},
                "track_ids": {}
            }

        classes = boxes.cls.cpu().numpy().astype(int)

        if boxes.id is not None:
            ids = boxes.id.cpu().numpy().astype(int)
        else:
            ids = [-1] * len(classes)

        counts = defaultdict(int)
        track_ids = defaultdict(list)

        for cls, track_id in zip(classes, ids):

            class_name = self.class_names[cls]

            counts[class_name] += 1

            if track_id != -1:
                track_ids[class_name].append(int(track_id))

        return {
            "counts": dict(counts),
            "track_ids": dict(track_ids)
        }
