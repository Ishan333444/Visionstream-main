import cv2
import time

from backend.config.settings import Settings
from backend.config.config_loader import (
    load_calibration,
    scale_point,
    scale_polygon,
)

from backend.detector.yolo_detector import YOLODetector

from backend.analytics.object_counter import ObjectCounter
from backend.analytics.line_counter import LineCounter
from backend.analytics.intrusion_detector import IntrusionDetector
from backend.analytics.dwell_timer import DwellTimer
from backend.analytics.crowd_density import CrowdDensity
from backend.analytics.heatmaps import Heatmap

from backend.visualization.overlay import Overlay

from backend.services.analytics_repository import update_latest
from backend.services.event_repository import log_event
from backend.services.frame_manager import set_frame


class VisionEngine:

    def __init__(self):

        # ----------------------------------
        # Detector
        # ----------------------------------

        self.detector = YOLODetector(Settings.MODEL_PATH)

        # ----------------------------------
        # Camera
        # ----------------------------------

        self.cap = cv2.VideoCapture(Settings.CAMERA_SOURCE)

        ret, frame = self.cap.read()

        if not ret:
            raise RuntimeError("Could not open camera.")

        height, width = frame.shape[:2]

        # ----------------------------------
        # Calibration
        # ----------------------------------

        calibration = load_calibration()

        line = calibration["entry_line"]

        line_start = scale_point(
            line["start"],
            width,
            height
        )

        line_end = scale_point(
            line["end"],
            width,
            height
        )

        polygon = scale_polygon(
            calibration["intrusion_zone"],
            width,
            height
        )

        # ----------------------------------
        # Analytics Modules
        # ----------------------------------

        self.counter = ObjectCounter(
            self.detector.class_names
        )

        self.line_counter = LineCounter(
            start=line_start,
            end=line_end,
            margin=Settings.LINE_MARGIN,
            confirm_frames=Settings.LINE_CONFIRM_FRAMES,
        )

        self.intrusion_detector = IntrusionDetector(
            polygon
        )

        self.dwell_timer = DwellTimer()

        self.crowd_density = CrowdDensity(
   	     Settings.CROWD_LOW,
   	     Settings.CROWD_MEDIUM
	)

        self.heatmap = Heatmap(
    	     frame.shape[1],
  	     frame.shape[0],
  	     radius=Settings.HEATMAP_RADIUS
	)

        # ----------------------------------
        # Timing
        # ----------------------------------

        self.prev_time = time.time()

        self.last_db_update = time.time()

    def run(self):

        while True:

            ret, frame = self.cap.read()

            if not ret:
                break

            # ----------------------------------
            # Detection + Tracking
            # ----------------------------------

            results = self.detector.track(frame)

            annotated = results[0].plot()

            # ----------------------------------
            # Analytics
            # ----------------------------------

            object_data = self.counter.count(results)

            line_data = self.line_counter.update(results)

            intrusion_data = self.intrusion_detector.update(results)

            dwell_data = self.dwell_timer.update(
                intrusion_data["inside_ids"]
            )

            object_counts = object_data["counts"]

            density = self.crowd_density.calculate(
                object_counts
            )

            person_count = object_counts.get(
                "person",
                0
            )

            # ----------------------------------
            # FPS
            # ----------------------------------

            current_time = time.time()

            fps = 1 / (
                current_time - self.prev_time
            )

            self.prev_time = current_time

            # ----------------------------------
            # Database
            # ----------------------------------

            if (
                current_time - self.last_db_update
                >= Settings.DATABASE_UPDATE_INTERVAL
            ):

                update_latest(
                    people=person_count,
                    entries=line_data["entries"],
                    exits=line_data["exits"],
                    inside_zone=intrusion_data["inside"],
                    density=density["density"],
                    object_counts=object_counts,
                )

                self.last_db_update = current_time

            # ----------------------------------
            # Heatmap
            # ----------------------------------

            self.heatmap.update(
                line_data["feet"]
            )

            # ----------------------------------
            # Line Events
            # ----------------------------------

            for track_id in line_data["entered_ids"]:

                log_event(
                    event_type="line_entry",
                    track_id=int(track_id),
                    source="line_counter"
                )

            for track_id in line_data["exited_ids"]:

                log_event(
                    event_type="line_exit",
                    track_id=int(track_id),
                    source="line_counter"
                )

            # ----------------------------------
            # Intrusion Events
            # ----------------------------------

            for track_id in intrusion_data["entered"]:

                log_event(
                    event_type="entered_zone",
                    track_id=int(track_id),
                    source="intrusion_detector"
                )

            for track_id in intrusion_data["exited"]:

                log_event(
                    event_type="exited_zone",
                    track_id=int(track_id),
                    source="intrusion_detector"
                )

            # ----------------------------------
            # Draw Overlay
            # ----------------------------------

            annotated = Overlay.draw(
                frame=annotated,
                fps=fps,
                people_count=person_count,
                line_data=line_data,
                intrusion_data=intrusion_data,
                dwell_data=dwell_data,
                line_counter=self.line_counter,
                intrusion_detector=self.intrusion_detector
            )

            # ----------------------------------
            # Heatmap Overlay
            # ----------------------------------

            annotated = self.heatmap.overlay(
                annotated,
                alpha=Settings.HEATMAP_ALPHA
            )

            # ----------------------------------
            # Streamlit Frame
            # ----------------------------------

            set_frame(annotated)

            # ----------------------------------
            # Local Display (Optional)
            # ----------------------------------

            if Settings.SHOW_WINDOW:

                cv2.imshow(
                    "VisionStream",
                    annotated
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        self.cap.release()

        if Settings.SHOW_WINDOW:
            cv2.destroyAllWindows()
