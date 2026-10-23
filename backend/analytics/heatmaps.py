import cv2
import numpy as np


class Heatmap:
    """Accumulate foot-point activity and blend it only over visited pixels."""

    def __init__(self, width, height, radius=20):
        self.width = width
        self.height = height
        self.radius = radius
        self.map = np.zeros((height, width), dtype=np.float32)

    def update(self, feet):
        # Build this frame's activity mask, then accumulate it. A pixel is
        # incremented at most once per frame, even if several points overlap.
        frame_activity = np.zeros_like(self.map)

        for x, y in feet:
            cv2.circle(
                frame_activity,
                (int(x), int(y)),
                self.radius,
                1.0,
                -1,
            )

        self.map += frame_activity

    def overlay(self, frame, alpha=0.4):
        # An empty map should leave the original frame untouched.
        active_pixels = self.map > 0
        if not np.any(active_pixels):
            return frame.copy()

        heatmap = cv2.normalize(
            self.map,
            None,
            0,
            255,
            cv2.NORM_MINMAX,
        ).astype(np.uint8)

        colored_heatmap = cv2.applyColorMap(
            heatmap,
            cv2.COLORMAP_JET,
        )

        blended = cv2.addWeighted(
            frame,
            1 - alpha,
            colored_heatmap,
            alpha,
            0,
        )

        # Blend only where activity has accumulated; don't tint untouched areas.
        output = frame.copy()
        output[active_pixels] = blended[active_pixels]
        return output
