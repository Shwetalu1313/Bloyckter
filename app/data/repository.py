import os
from cryptography.fernet import Fernet
import json
import app.core.security.dpapi as dpapi
from config import DATA_FILE
from app.core.security.security_service import SecurityService # For permission hardening 

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

    if not os.path.exists(DATA_FILE):
        return {}

    try:
        cipher = dpapi.get_cipher()

        with open(DATA_FILE, "rb") as f:
            encrypted = f.read()

        decrypted = cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())

    except Exception:
        # Any error = treat as empty data
        # (wrong key, tampered file, corrupted file)
        return {}


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

    # Write to disk
    with open(DATA_FILE, "wb") as f:
        f.write(encrypted)

    # Lock down permissions
    SecurityService.restrict_permission(DATA_FILE)