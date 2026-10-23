"""Load and atomically persist the preferred inference device."""

import json
import os
from pathlib import Path
import tempfile

from backend.config.settings import Settings

VALID_DEVICE_SETTINGS = {"auto", "cpu", "cuda"}


def _settings_path(path=None):
    candidate = Path(path or Settings.DEVICE_SETTINGS_PATH)
    if not candidate.is_absolute():
        # Resolve relative paths from the project root, not the shell's current directory.
        project_root = Path(__file__).resolve().parents[2]
        candidate = project_root / candidate
    return candidate


def load_device_setting(default=None, path=None):
    """Return the saved device preference, or the configured default if absent/invalid."""
    fallback = (default or Settings.DEVICE).strip().lower()
    try:
        payload = json.loads(_settings_path(path).read_text(encoding="utf-8"))
        setting = str(payload.get("device", "")).strip().lower()
        if setting in VALID_DEVICE_SETTINGS:
            return setting
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return fallback if fallback in VALID_DEVICE_SETTINGS else "auto"


def save_device_setting(device, path=None):
    """Persist a validated preference with an atomic replace to avoid partial files."""
    setting = str(device).strip().lower()
    if setting not in VALID_DEVICE_SETTINGS:
        raise ValueError(f"Unsupported device setting: {setting}")

    destination = _settings_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent,
            prefix=destination.name + ".", suffix=".tmp", delete=False
        ) as temp_file:
            json.dump({"device": setting}, temp_file, indent=2)
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_name = temp_file.name
        os.replace(temp_name, destination)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    return setting
