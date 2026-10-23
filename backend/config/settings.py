class Settings:

    MODEL_PATH = "models/yolo11n.pt"

    # Compute Device
    # "auto" = use a supported GPU backend when available, otherwise CPU
    # "cpu" = force CPU
    # "cuda" = explicitly request a compatible NVIDIA CUDA setup
    # This dashboard build does not expose a separate ROCm selection; Auto can
    # still use a compatible HIP-backed PyTorch build on supported Linux systems.
    DEVICE = "auto"
    # Persistent runtime device preference is stored separately from this source file.
    DEVICE_SETTINGS_PATH = "backend/config/device_settings.json"

    CAMERA_SOURCE = 0
    # Camera startup and recovery policy. Live sources are retried; finite video
    # files stop at EOF instead of being reopened and replayed from the start.
    CAMERA_OPEN_MAX_ATTEMPTS = 5
    CAMERA_RECONNECT_MAX_ATTEMPTS = 5
    CAMERA_RECONNECT_INITIAL_DELAY_SECONDS = 1.0
    CAMERA_RECONNECT_MAX_DELAY_SECONDS = 10.0
    CAMERA_READ_FAILURES_BEFORE_RECONNECT = 3
    CAMERA_READ_FAILURE_RETRY_DELAY_SECONDS = 0.1

    # Entry / Exit Line
    LINE_MARGIN = 25
    LINE_CONFIRM_FRAMES = 3
    # Retain line-crossing state through short tracking gaps, then prune it.
    LINE_TRACK_STATE_MAX_AGE_SECONDS = 30.0

    HEATMAP_RADIUS = 20
    HEATMAP_ALPHA = 0.35

    DETECTION_CONFIDENCE = 0.25
    DETECTION_IOU = 0.45

    CROWD_LOW = 2
    CROWD_MEDIUM = 5

    DATABASE_UPDATE_INTERVAL = 0.2

    # Keep a temporarily missing intrusion-zone track for this long before
    # treating it as an exit.
    INTRUSION_MISSING_GRACE_SECONDS = 1.0
    SHOW_WINDOW = False