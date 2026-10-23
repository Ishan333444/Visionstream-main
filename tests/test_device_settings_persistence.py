import json

import pytest

from backend.config.device_settings import load_device_setting, save_device_setting


def test_missing_file_uses_default(tmp_path):
    path = tmp_path / "device_settings.json"
    assert load_device_setting("auto", path=path) == "auto"


def test_saved_device_survives_reload(tmp_path):
    path = tmp_path / "device_settings.json"
    assert save_device_setting("cpu", path=path) == "cpu"
    assert load_device_setting("auto", path=path) == "cpu"
    assert json.loads(path.read_text(encoding="utf-8")) == {"device": "cpu"}


def test_invalid_saved_value_uses_default(tmp_path):
    path = tmp_path / "device_settings.json"
    path.write_text('{"device": "tpu"}', encoding="utf-8")
    assert load_device_setting("auto", path=path) == "auto"


def test_corrupt_file_uses_default(tmp_path):
    path = tmp_path / "device_settings.json"
    path.write_text('{not json', encoding="utf-8")
    assert load_device_setting("cpu", path=path) == "cpu"


def test_unsupported_value_cannot_be_saved(tmp_path):
    with pytest.raises(ValueError, match="Unsupported device setting"):
        save_device_setting("tpu", path=tmp_path / "device_settings.json")


def test_save_replaces_existing_setting_atomically(tmp_path):
    path = tmp_path / "device_settings.json"
    save_device_setting("cpu", path=path)
    save_device_setting("auto", path=path)
    assert load_device_setting("cpu", path=path) == "auto"
    assert list(tmp_path.glob("*.tmp")) == []


def test_legacy_rocm_preference_is_ignored_by_current_selector(tmp_path):
    path = tmp_path / "device_settings.json"
    path.write_text('{"device": "rocm"}', encoding="utf-8")
    assert load_device_setting("auto", path=path) == "auto"
