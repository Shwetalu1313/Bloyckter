import os
import json
import shutil
import tempfile
import app.core.security.dpapi as dpapi
from config import DATA_FILE, DATA_FILE_BACKUP
from app.core.security.security_service import SecurityService  # For permission hardening

# ======================================================
# Encrypted data loading
# ======================================================
def load_data():
    """
    Loads and decrypts application data from disk.

    Behavior:
    - If file does not exist → return empty dict
    - If file is corrupted / key missing → fail safely
      by returning empty dict

    IMPORTANT:
    - This prevents crashes
    - Data loss is safer than data exposure
    """

    primary = _load_file(DATA_FILE)
    if primary is not None:
        return primary

    backup = _load_file(DATA_FILE_BACKUP)
    return backup if backup is not None else {}


def _load_file(path: str):
    if not os.path.exists(path):
        return None

    try:
        cipher = dpapi.get_cipher()
        with open(path, "rb") as file_obj:
            encrypted = file_obj.read()
        decrypted = cipher.decrypt(encrypted)
        data = json.loads(decrypted.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return None


# ======================================================
# Encrypted data saving
# ======================================================
def save_data(data: dict):
    """
    Encrypts and saves application data to disk.

    Steps:
    1. Convert dict → JSON
    2. Encrypt JSON using Fernet (AES)
    3. Write encrypted bytes to disk
    4. Restrict file permissions
    """

    cipher = dpapi.get_cipher()

    # Serialize → bytes
    raw = json.dumps(data).encode()

    # Encrypt
    encrypted = cipher.encrypt(raw)

    if os.path.exists(DATA_FILE):
        shutil.copy2(DATA_FILE, DATA_FILE_BACKUP)

    _atomic_write(DATA_FILE, encrypted)


def _atomic_write(path: str, payload: bytes):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temp_path = None
    fd = None

    try:
        fd, temp_path = tempfile.mkstemp(prefix="vault_", suffix=".tmp", dir=directory)
        with os.fdopen(fd, "wb") as tmp_file:
            fd = None
            tmp_file.write(payload)
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
