import torch
from ultralytics import YOLO

from backend.config.settings import Settings


def resolve_device():
    if Settings.DEVICE == "cpu":
        return "cpu"

    if Settings.DEVICE == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA device requested, but no CUDA-compatible "
                "PyTorch device is available."
            )
        return "cuda"

    if Settings.DEVICE == "auto":
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    raise ValueError(
        f"Unsupported device setting: {Settings.DEVICE}"
    )


class YOLODetector:

    def __init__(self, model_path):
        self.device = resolve_device()

        print(f"VisionStream device: {self.device}")

        self.model = YOLO(model_path)
        self.class_names = self.model.names

    def detect(self, frame):
        return self.model(
            frame,
            device=self.device,
            verbose=False
        )

    def track(self, frame):
        return self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            device=self.device,
            verbose=False
        )