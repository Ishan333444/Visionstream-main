from types import SimpleNamespace
import sys
import types

import pytest

# Keep device-selection tests independent of the heavyweight inference package.
if "ultralytics" not in sys.modules:
    ultralytics_stub = types.ModuleType("ultralytics")
    ultralytics_stub.YOLO = object
    sys.modules["ultralytics"] = ultralytics_stub
if "torch" not in sys.modules:
    torch_stub = types.ModuleType("torch")
    torch_stub.cuda = SimpleNamespace(is_available=lambda: False)
    torch_stub.version = SimpleNamespace(hip=None)
    sys.modules["torch"] = torch_stub

from backend.detector import yolo_detector


class FakeTorch:
    def __init__(self, available, hip=None):
        self.cuda = SimpleNamespace(is_available=lambda: available)
        self.version = SimpleNamespace(hip=hip)


def test_cpu_is_always_available(monkeypatch):
    monkeypatch.setattr(yolo_detector, "torch", FakeTorch(False))
    assert yolo_detector.resolve_device("cpu") == "cpu"


def test_auto_falls_back_to_cpu(monkeypatch):
    monkeypatch.setattr(yolo_detector, "torch", FakeTorch(False))
    assert yolo_detector.resolve_device("auto") == "cpu"


def test_auto_uses_cuda_device_string_for_rocm_build(monkeypatch):
    monkeypatch.setattr(yolo_detector, "torch", FakeTorch(True, hip="6.2"))
    assert yolo_detector.resolve_device("auto") == "cuda"
    assert yolo_detector.describe_device("auto")["label"] == "AMD GPU (ROCm/HIP)"


def test_rocm_is_not_an_explicitly_selectable_device(monkeypatch):
    monkeypatch.setattr(yolo_detector, "torch", FakeTorch(False, hip=None))
    with pytest.raises(ValueError, match="Unsupported device setting: rocm"):
        yolo_detector.resolve_device("rocm")


def test_cuda_selection_rejects_rocm_build(monkeypatch):
    monkeypatch.setattr(yolo_detector, "torch", FakeTorch(True, hip="6.2"))
    with pytest.raises(RuntimeError, match="ROCm/HIP build"):
        yolo_detector.resolve_device("cuda")


def test_cuda_selection_requires_available_device(monkeypatch):
    monkeypatch.setattr(yolo_detector, "torch", FakeTorch(False, hip=None))
    with pytest.raises(RuntimeError, match="no CUDA-compatible"):
        yolo_detector.resolve_device("cuda")


def test_unknown_device_is_rejected(monkeypatch):
    monkeypatch.setattr(yolo_detector, "torch", FakeTorch(False))
    with pytest.raises(ValueError, match="Unsupported device setting"):
        yolo_detector.resolve_device("tpu")
