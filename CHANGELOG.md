# VisionStream — Update Log

## Current update

### Dashboard and calibration
- Added a Streamlit calibration page for configuring line and polygon geometry.
- Added support for multiple named entry/exit counting lines.
- Added support for multiple named intrusion zones.
- Added validation and normalized frame coordinates for calibration geometry.
- Added a calibration API and persistent calibration configuration.
- Added compatibility/migration handling for the prior single-line/single-zone configuration.

### Compute device settings
- Added a dashboard selector for Auto, CPU, and NVIDIA CUDA.
- Removed the explicit AMD ROCm option from this Windows-oriented build.
- Added a device settings service/API and persistent preference storage.
- Added validation and runtime status reporting for the selected/active device.
- Added detector initialization safeguards so a failed device change can be rejected rather than silently pretending to succeed.

### Detection and camera reliability
- Wired configured YOLO confidence and IoU thresholds into detection and tracking calls.
- Added bounded camera open/reconnect retries with delays and logging.
- Added handling for temporary camera read failures and clean shutdown behavior.

### Analytics fixes
- Added a grace period for brief missed intrusion tracks to reduce false exits and dwell-timer resets.
- Changed heatmaps to accumulate activity over time and blend only visited pixels.
- Added finite-segment checks so line crossings beyond configured endpoints are not counted.
- Reset interrupted line-crossing confirmation streaks when observations fall into the neutral margin.
- Added cleanup of stale per-track line-counter state after a configurable timeout.

### Tests
- Added/updated targeted regression tests covering device selection and persistence, calibration configuration, multiple lines and zones, camera recovery, detector thresholds, line counting, intrusion handling, and heatmaps.

## Validation notes and limitations
- The archive and Python compilation were reported as checked during the update workflow; targeted tests were reported passing in that workflow.
- Tests with simulated devices do not prove that GPU inference works on a particular machine.
- The current Windows environment reported PyTorch `2.14.1+cpu`, with no HIP backend and no GPU available to PyTorch. Therefore, this environment currently runs inference on CPU.
- Actual camera reconnection and the complete Streamlit experience should still be verified on the target machine.
- A full test-suite collection previously encountered a local SQLite issue because the `analytics` table was missing. This remains a separate integration check.
