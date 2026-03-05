import os
import ctypes
from pathlib import Path
from typing import Optional


# Windows drive type constant returned by GetDriveTypeW
DRIVE_REMOTE = 4

# Common remote filesystem types for Linux/macOS-style mount tables.
REMOTE_FS_TYPES = {
    "nfs",
    "nfs4",
    "cifs",
    "smbfs",
    "sshfs",
    "fuse.sshfs",
    "afpfs",
    "davfs",
    "ceph",
    "glusterfs",
}


def _is_unc_path(path: str) -> bool:
    return path.startswith("\\\\")


def _get_windows_drive(path: str) -> Optional[str]:
    drive, _ = os.path.splitdrive(path)
    if not drive:
        return None
    return f"{drive}\\"


def _is_windows_remote_drive(path: str) -> bool:
    drive_root = _get_windows_drive(path)
    if not drive_root:
        return False

    try:
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_root)
    except Exception:
        return False
    return drive_type == DRIVE_REMOTE


def _parse_mount_table() -> list[tuple[str, str]]:
    mounts: list[tuple[str, str]] = []
    for table_path in ("/proc/mounts", "/etc/mtab"):
        if not os.path.exists(table_path):
            continue
        try:
            with open(table_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 3:
                        mount_point = parts[1].replace("\\040", " ")
                        fs_type = parts[2].lower()
                        mounts.append((mount_point, fs_type))
            if mounts:
                break
        except OSError:
            continue
    return mounts


def _is_posix_remote_mount(path: str) -> bool:
    try:
        resolved = str(Path(path).resolve())
    except Exception:
        resolved = os.path.abspath(path)

    best_match = ""
    best_fs = None
    for mount_point, fs_type in _parse_mount_table():
        if resolved == mount_point or resolved.startswith(f"{mount_point.rstrip('/')}/"):
            if len(mount_point) > len(best_match):
                best_match = mount_point
                best_fs = fs_type
    return bool(best_fs and best_fs in REMOTE_FS_TYPES)


def is_remote_mount_path(path: str) -> bool:
    normalized = os.path.abspath(path)
    if _is_unc_path(normalized):
        return True

    if os.name == "nt":
        return _is_windows_remote_drive(normalized)
    return _is_posix_remote_mount(normalized)


def is_remote_mount_root(path: str) -> bool:
    normalized = os.path.abspath(path)
    return os.path.ismount(normalized) and is_remote_mount_path(normalized)


def test_path_connection(path: str) -> tuple[bool, str]:
    target = os.path.abspath((path or "").strip().strip('"'))
    if not target:
        return False, "Path is required."

    if not os.path.exists(target):
        return False, f"Path not reachable: {target}"

    try:
        if os.path.isdir(target):
            with os.scandir(target) as scan_it:
                next(scan_it, None)
        else:
            with open(target, "rb"):
                pass
    except PermissionError:
        return False, f"Path reachable but access denied: {target}"
    except OSError as ex:
        return False, f"Path reachable but check failed: {ex}"

    if is_remote_mount_path(target):
        return True, f"Remote path is reachable: {target}"
    return True, f"Path is reachable: {target}"
