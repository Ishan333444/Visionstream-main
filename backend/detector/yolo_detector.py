import torch
from ultralytics import YOLO

from backend.config.settings import Settings

SUPPORTED_DEVICE_SETTINGS = ("auto", "cpu", "cuda")


def _is_rocm_build():
    """PyTorch's ROCm build exposes devices through its CUDA-compatible API."""
    return bool(getattr(getattr(torch, "version", None), "hip", None))


def resolve_device(device_setting=None):
    setting = (device_setting or Settings.DEVICE).lower()

    if setting not in SUPPORTED_DEVICE_SETTINGS:
        raise ValueError(
            f"Unsupported device setting: {setting}. Choose one of: "
            f"{', '.join(SUPPORTED_DEVICE_SETTINGS)}"
        )

    if setting == "cpu":
        return "cpu"

    if setting == "cuda":
        if _is_rocm_build():
            raise RuntimeError(
                "NVIDIA CUDA was requested, but this PyTorch installation is a "
                "ROCm/HIP build. Select Auto instead."
            )
        if not torch.cuda.is_available():
            raise RuntimeError(
                "NVIDIA CUDA was requested, but no CUDA-compatible PyTorch "
                "device is available."
            )
        return "cuda"

    # Auto: use the available CUDA-compatible backend (CUDA or ROCm), else CPU.
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def describe_device(device_setting=None):
    setting = (device_setting or Settings.DEVICE).lower()
    resolved = resolve_device(setting)
    if resolved == "cpu":
        label = "CPU"
    elif _is_rocm_build():
        label = "AMD GPU (ROCm/HIP)"
    else:
        label = "NVIDIA GPU (CUDA)"
    return {"setting": setting, "resolved_device": resolved, "label": label}


class YOLODetector:

    def __init__(self, model_path, device_setting=None):
        self.device_setting = (device_setting or Settings.DEVICE).lower()
        self.device = resolve_device(self.device_setting)

        print(f"VisionStream device: {describe_device(self.device_setting)['label']} ({self.device})")

        self.model = YOLO(model_path)
        self.class_names = self.model.names

    def detect(self, frame):
        return self.model(
            frame,
            conf=Settings.DETECTION_CONFIDENCE,
            iou=Settings.DETECTION_IOU,
            device=self.device,
            verbose=False
        )

    def track(self, frame):
        return self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=Settings.DETECTION_CONFIDENCE,
            iou=Settings.DETECTION_IOU,
            device=self.device,
            verbose=False
        )
