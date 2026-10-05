class Settings:

    MODEL_PATH = "models/yolo11n.pt"

    # Compute Device
    # "auto" = automatically select the best available device
    # "cpu"  = force CPU
    # "cuda" = force CUDA / supported GPU backend
    DEVICE = "auto"

    CAMERA_SOURCE = 0

    # Entry / Exit Line
    LINE_MARGIN = 25
    LINE_CONFIRM_FRAMES = 3

    HEATMAP_RADIUS = 20
    HEATMAP_ALPHA = 0.35

    DETECTION_CONFIDENCE = 0.25
    DETECTION_IOU = 0.45

    CROWD_LOW = 2
    CROWD_MEDIUM = 5

    DATABASE_UPDATE_INTERVAL = 0.2
    SHOW_WINDOW = True