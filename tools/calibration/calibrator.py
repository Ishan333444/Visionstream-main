import cv2
import json
import numpy as np
from pathlib import Path


CONFIG_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "backend"
    / "config"
    / "calibration.json"
)


class Calibrator:

    def __init__(self):

        self.cap = cv2.VideoCapture(Settings.CAMERA_SOURCE)

        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera.")

        cv2.namedWindow("VisionStream Calibration")

        print("Press SPACE to freeze the frame.")

        while True:

            success, frame = self.cap.read()

            if not success:
                self.cap.release()
                cv2.destroyAllWindows()
                raise RuntimeError("Failed to read camera.")

            preview = frame.copy()

            cv2.putText(
                preview,
                "Press SPACE to freeze frame",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "VisionStream Calibration",
                preview
            )

            key = cv2.waitKey(20) & 0xFF

            if key == 32:      # SPACE
                self.frame = frame.copy()
                break

            elif key == 27:
                self.cap.release()
                cv2.destroyAllWindows()
                raise SystemExit

        self.display = self.frame.copy()

        self.height, self.width = self.frame.shape[:2]

        self.stage = "line"

        self.line_points = []
        self.polygon_points = []

        cv2.namedWindow("VisionStream Calibration")
        cv2.setMouseCallback(
            "VisionStream Calibration",
            self.mouse_callback
        )

    def mouse_callback(self, event, x, y, flags, param):

        if event != cv2.EVENT_LBUTTONDOWN:
            return

        point = (x, y)

        if self.stage == "line":

            if len(self.line_points) < 2:
                self.line_points.append(point)

            if len(self.line_points) == 2:
                self.stage = "polygon"

        elif self.stage == "polygon":

            self.polygon_points.append(point)
    
    
    def redraw(self):

        self.display = self.frame.copy()

        # Draw line points
        for point in self.line_points:
            cv2.circle(
                self.display,
                point,
                5,
                (0, 0, 255),
                -1
            )

        # Draw entry line
        if len(self.line_points) == 2:
            cv2.line(
                self.display,
                self.line_points[0],
                self.line_points[1],
                (0, 0, 255),
                2
            )

        # Draw polygon vertices
        for point in self.polygon_points:
            cv2.circle(
                self.display,
                point,
                5,
                (0, 255, 0),
                -1
            )

        # Connect polygon edges
        if len(self.polygon_points) >= 2:

            cv2.polylines(
                self.display,
                [np.array(self.polygon_points, dtype=np.int32)],
                len(self.polygon_points) >= 3,
                (0,255,0),
                2
            )

        # UI text
        cv2.putText(
            self.display,
            "Stage 1/2: Draw Entry Line"
            if self.stage == "line"
            else "Stage 2/2: Draw Intrusion Zone",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.putText(
            self.display,
            "LMB:Add  Enter:Save  Backspace:Undo  R:Reset  Esc:Exit",
            (20, self.height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255,255,255),
            2
        )

    def save(self):

        def normalize(point):

            return [
                point[0] / self.width,
                point[1] / self.height
            ]

        data = {
            "entry_line": {
                "start": normalize(self.line_points[0]),
                "end": normalize(self.line_points[1]),
            },
            "intrusion_zone": [
                normalize(point)
                for point in self.polygon_points
            ],
        }

        CONFIG_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(CONFIG_PATH, "w") as file:

            json.dump(
                data,
                file,
                indent=4
            )

    def run(self):

        while True:

            self.redraw()

            cv2.imshow(
                "VisionStream Calibration",
                self.display
            )

            key = cv2.waitKey(20) & 0xFF

            # ESC
            if key == 27:
                break

            # Backspace
            elif key == 8:

                if self.stage == "polygon":

                    if self.polygon_points:
                        self.polygon_points.pop()

                    else:
                        self.stage = "line"
                        if self.line_points:
                            self.line_points.pop()
                
                elif self.stage == "line":

                    if self.line_points:
                        self.line_points.pop()

            # R
            elif key == ord("r"):

                self.stage = "line"

                self.line_points.clear()
                self.polygon_points.clear()

            # Enter
            elif key == 13:

                if (
                    self.stage == "polygon"
                    and len(self.line_points) == 2
                    and len(self.polygon_points) >= 3
                ):

                    self.save()

                    print(f"Calibration saved to:\n{CONFIG_PATH}")

                    break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    Calibrator().run()
