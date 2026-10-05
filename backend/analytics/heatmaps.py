import cv2
import numpy as np


class Heatmap:

    def __init__(self, width, height, radius=20):
        self.width = width
        self.height = height
        self.radius = radius
        self.map = np.zeros((height, width), dtype=np.float32)

    def update(self, feet):

        for x, y in feet:
            cv2.circle(
                self.map,
                (x, y),
                self.radius,
                1,
                -1
            )

    def overlay(self, frame, alpha=0.4):

        heatmap = cv2.normalize(
            self.map,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(np.uint8)

        heatmap = cv2.applyColorMap(
            heatmap,
            cv2.COLORMAP_JET
        )

        return cv2.addWeighted(
            frame,
            1 - alpha,
            heatmap,
            alpha,
            0
        )