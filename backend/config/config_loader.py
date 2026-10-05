import json
from pathlib import Path


CONFIG_PATH = Path(__file__).parent / "calibration.json"


def load_calibration():

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def scale_point(point, width, height):

    return (
        int(point[0] * width),
        int(point[1] * height)
    )


def scale_polygon(points, width, height):

    return [
        scale_point(point, width, height)
        for point in points
    ]
