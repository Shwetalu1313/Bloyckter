import json
import os
import tempfile
from config import SETTINGS_FILE
from app.core.security.security_service import SecurityService

DEFAULT_SETTINGS = {
    "workstation_auto_lock_enabled": False,
    "workstation_idle_minutes": 10,
}


def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file_obj:
            raw = json.load(file_obj)
        if not isinstance(raw, dict):
            return DEFAULT_SETTINGS.copy()
    except Exception:
        return DEFAULT_SETTINGS.copy()

    merged = DEFAULT_SETTINGS.copy()
    merged.update(raw)
    merged["workstation_auto_lock_enabled"] = bool(merged.get("workstation_auto_lock_enabled", False))
    merged["workstation_idle_minutes"] = _normalize_minutes(merged.get("workstation_idle_minutes", 10))
    return merged


def save_settings(settings: dict):
    normalized = {
        "workstation_auto_lock_enabled": bool(settings.get("workstation_auto_lock_enabled", False)),
        "workstation_idle_minutes": _normalize_minutes(settings.get("workstation_idle_minutes", 10)),
    }
    _atomic_write_json(SETTINGS_FILE, normalized)


def _normalize_minutes(value) -> int:
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        minutes = 10
    return min(max(minutes, 1), 240)


def _atomic_write_json(path: str, payload: dict):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temp_path = None
    fd = None

    try:
        fd, temp_path = tempfile.mkstemp(prefix="settings_", suffix=".tmp", dir=directory)
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            fd = None
            json.dump(payload, tmp_file, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        SecurityService.restrict_permission(temp_path)
        os.replace(temp_path, path)
        SecurityService.restrict_permission(path)
    finally:
        if fd is not None:
            os.close(fd)
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
