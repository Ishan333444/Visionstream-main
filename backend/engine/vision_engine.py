import cv2
import time
from threading import Lock


from backend.engine.camera_recovery import open_capture_with_retries, is_live_source

from backend.config.settings import Settings
from backend.config.device_settings import load_device_setting, save_device_setting
from backend.config.config_loader import (
    load_calibration,
    normalize_calibration,
    save_calibration,
)

from backend.detector.yolo_detector import YOLODetector, describe_device, resolve_device

from backend.analytics.object_counter import ObjectCounter
from backend.analytics.multi_line_counter import MultiLineCounter
from backend.analytics.multi_zone_detector import MultiZoneDetector
from backend.analytics.dwell_timer import DwellTimer
from backend.analytics.crowd_density import CrowdDensity
from backend.analytics.heatmaps import Heatmap

from backend.visualization.overlay import Overlay

from backend.services.analytics_repository import update_latest
from backend.services.event_repository import log_event
from backend.services.frame_manager import set_frame


class VisionEngine:

    def __init__(self):
        self._device_lock = Lock()
        self._pending_device_setting = None
        self._calibration_lock = Lock()
        self._pending_calibration = None
        self.calibration_change_status = "idle"
        self.calibration_change_error = None
        self.device_change_status = "idle"
        self.device_change_error = None
        preferred_device = load_device_setting(Settings.DEVICE)
        self.preferred_device_setting = preferred_device

        # ----------------------------------
        # Detector
        # ----------------------------------

        try:
            self.detector = YOLODetector(
                Settings.MODEL_PATH, device_setting=preferred_device
            )
            self.device_setting = self.detector.device_setting
        except (RuntimeError, ValueError) as exc:
            # Keep the saved preference for visibility, but don't make the whole
            # service unavailable if that hardware/backend isn't present at startup.
            if preferred_device == "auto":
                raise
            self.device_change_status = "failed"
            self.device_change_error = (
                f"Saved device preference '{preferred_device}' is unavailable: {exc}. "
                "Falling back to automatic device selection for this run."
            )
            print(f"[VisionStream] {self.device_change_error}")
            self.detector = YOLODetector(Settings.MODEL_PATH, device_setting="auto")
            self.device_setting = self.detector.device_setting

        # ----------------------------------
        # Camera
        # ----------------------------------

        self.source = Settings.CAMERA_SOURCE
        self.is_live_source = is_live_source(self.source)
        self.running = True
        self.cap, frame = open_capture_with_retries(
            source=self.source,
            max_attempts=Settings.CAMERA_OPEN_MAX_ATTEMPTS,
            initial_delay=Settings.CAMERA_RECONNECT_INITIAL_DELAY_SECONDS,
            max_delay=Settings.CAMERA_RECONNECT_MAX_DELAY_SECONDS,
        )

        height, width = frame.shape[:2]

        # ----------------------------------
        # Calibration
        # ----------------------------------

        calibration = load_calibration()
        self.calibration = calibration
        self.frame_width = width
        self.frame_height = height

        # ----------------------------------
        # Analytics Modules
        # ----------------------------------

        self.counter = ObjectCounter(
            self.detector.class_names
        )

        self.line_counter = MultiLineCounter(
            calibration["lines"], width, height
        )

        self.intrusion_detector = MultiZoneDetector(
            calibration["zones"], width, height
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

    def stop(self):
        """Request a graceful stop; run() performs capture/window cleanup."""
        self.running = False

    def get_calibration_status(self):
        with self._calibration_lock:
            pending = self._pending_calibration is not None
            status = self.calibration_change_status
            error = self.calibration_change_error
        return {
            "calibration": self.calibration,
            "status": status,
            "pending": pending,
            "error": error,
        }

    def request_calibration_update(self, calibration):
        normalized = normalize_calibration(calibration)
        with self._calibration_lock:
            self._pending_calibration = normalized
            self.calibration_change_status = "pending"
            self.calibration_change_error = None
        return self.get_calibration_status()

    def _apply_pending_calibration(self):
        """Apply a validated calibration at a frame boundary, preserving cumulative totals."""
        with self._calibration_lock:
            requested = self._pending_calibration
            if requested is None:
                return
            self._pending_calibration = None
            self.calibration_change_status = "applying"

        try:
            # Build the replacements before persisting so validation/initialization
            # failures cannot leave disk and the running engine out of sync.
            new_line_counter = MultiLineCounter(
                requested["lines"], self.frame_width, self.frame_height,
                previous=self.line_counter,
            )
            new_zone_detector = MultiZoneDetector(
                requested["zones"], self.frame_width, self.frame_height,
            )
            # If the atomic write fails, keep the currently active calibration.
            save_calibration(requested)
            self.line_counter = new_line_counter
            self.intrusion_detector = new_zone_detector
            self.dwell_timer.entry_times.clear()
            self.calibration = requested
            with self._calibration_lock:
                self.calibration_change_status = "applied"
                self.calibration_change_error = None
            print("[VisionStream] Calibration updated successfully")
        except Exception as exc:
            with self._calibration_lock:
                self.calibration_change_status = "failed"
                self.calibration_change_error = str(exc)
            print(f"[VisionStream] Calibration update failed; keeping active configuration: {exc}")

    def get_device_status(self):
        """Return current device and any pending device change for the dashboard."""
        with self._device_lock:
            pending = self._pending_device_setting
            status = self.device_change_status
            error = self.device_change_error
            current_setting = self.device_setting
        info = describe_device(current_setting)
        info.update({
            "status": status,
            "pending_setting": pending,
            "error": error,
            "preferred_setting": load_device_setting(Settings.DEVICE),
            "supported_settings": ["auto", "cpu", "cuda"],
        })
        return info

    def request_device_change(self, device_setting):
        """Validate and queue a device change; the engine applies it between frames."""
        setting = str(device_setting).strip().lower()
        # Validate availability before accepting the request. No model is changed here.
        resolve_device(setting)
        with self._device_lock:
            if setting == self.device_setting and self._pending_device_setting is None:
                self.device_change_status = "idle"
                self.device_change_error = None
            else:
                self._pending_device_setting = setting
                self.device_change_status = "pending"
                self.device_change_error = None
        return self.get_device_status()

    def _apply_pending_device_change(self, frame):
        """Rebuild and smoke-test a detector at a frame boundary; preserve old model on failure."""
        with self._device_lock:
            requested = self._pending_device_setting
            if requested is None:
                return None
            self._pending_device_setting = None
            self.device_change_status = "applying"

        try:
            replacement = YOLODetector(
                Settings.MODEL_PATH,
                device_setting=requested,
            )
            # A real inference on the current frame catches backend/device failures
            # before the replacement becomes active, and avoids processing this frame twice.
            first_results = replacement.track(frame)

            # A new YOLO tracker starts with fresh IDs. Clear per-track state so IDs
            # from the previous tracker session cannot be mistaken for new tracks.
            self.line_counter.reset_tracks()
            self.intrusion_detector.reset_tracking()
            self.dwell_timer.entry_times.clear()
            # Persist only after the replacement detector has passed its smoke test,
            # but before swapping the active detector. If disk persistence fails, the
            # old detector remains active and the change is reported as failed.
            save_device_setting(requested)
            self.detector = replacement
            self.device_setting = requested
            self.preferred_device_setting = requested
            Settings.DEVICE = requested
            with self._device_lock:
                self.device_change_status = "applied"
                self.device_change_error = None
            print(f"[VisionStream] Compute device changed to {describe_device(requested)['label']}")
            return first_results
        except Exception as exc:
            with self._device_lock:
                self.device_change_status = "failed"
                self.device_change_error = str(exc)
            print(f"[VisionStream] Device change failed; keeping previous detector: {exc}")
            return None

    def _reconnect_camera(self):
        """Try a bounded reconnect sequence; return the first recovered frame or None."""
        try:
            self.cap.release()
        except Exception:
            pass

        delay = Settings.CAMERA_RECONNECT_INITIAL_DELAY_SECONDS
        attempts = max(1, int(Settings.CAMERA_RECONNECT_MAX_ATTEMPTS))
        for attempt in range(1, attempts + 1):
            if not self.running:
                return None
            print(f"[VisionStream] Camera reconnect attempt {attempt}/{attempts}")
            try:
                self.cap, frame = open_capture_with_retries(
                    source=self.source,
                    max_attempts=1,
                    initial_delay=delay,
                    max_delay=Settings.CAMERA_RECONNECT_MAX_DELAY_SECONDS,
                )
                print("[VisionStream] Camera reconnected successfully")
                return frame
            except RuntimeError as exc:
                print(f"[VisionStream] Camera reconnect failed: {exc}")
                if attempt < attempts:
                    time.sleep(delay)
                    delay = min(
                        Settings.CAMERA_RECONNECT_MAX_DELAY_SECONDS,
                        max(delay * 2, 0.1),
                    )
        print("[VisionStream] Camera unavailable after reconnect attempts; stopping engine")
        return None

    def run(self):
        consecutive_read_failures = 0
        pending_frame = None

        try:
            while self.running:
                if pending_frame is not None:
                    frame = pending_frame
                    pending_frame = None
                    ret = True
                else:
                    ret, frame = self.cap.read()

                if not ret or frame is None:
                    consecutive_read_failures += 1
                    print(
                        f"[VisionStream] Frame read failed "
                        f"({consecutive_read_failures}/"
                        f"{Settings.CAMERA_READ_FAILURES_BEFORE_RECONNECT})"
                    )

                    # A file reaching EOF is expected; don't reopen it and replay it.
                    if not self.is_live_source:
                        break

                    if consecutive_read_failures < Settings.CAMERA_READ_FAILURES_BEFORE_RECONNECT:
                        time.sleep(Settings.CAMERA_READ_FAILURE_RETRY_DELAY_SECONDS)
                        continue

                    pending_frame = self._reconnect_camera()
                    consecutive_read_failures = 0
                    if pending_frame is None:
                        break
                    continue

                consecutive_read_failures = 0
                self._apply_pending_calibration()

                # ----------------------------------
                # Detection + Tracking
                # ----------------------------------

                results = self._apply_pending_device_change(frame)
                if results is None:
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

                # Log each line crossing separately, including its line ID, so a
                # person crossing two configured lines can produce two traceable events.
                for line_event in line_data.get("per_line", []):
                    source = f"line_counter:{line_event['id']}"
                    for track_id in line_event["entered_ids"]:
                        log_event(
                            event_type="line_entry",
                            track_id=int(track_id),
                            source=source,
                        )
                    for track_id in line_event["exited_ids"]:
                        log_event(
                            event_type="line_exit",
                            track_id=int(track_id),
                            source=source,
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

        finally:
            try:
                self.cap.release()
            except Exception:
                pass

            if Settings.SHOW_WINDOW:
                cv2.destroyAllWindows()
