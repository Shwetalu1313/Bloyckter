"""
helper.py
==========

This module is responsible for:
- Secure key storage (Windows DPAPI)
- Encrypted data storage (Fernet / AES)
- File system location management (AppData)
- Password hashing
- Permission hardening

IMPORTANT DESIGN RULE:
This file contains NO GUI logic and NO business logic.
It only provides reusable helper utilities.
"""

# =========================
# Standard library imports
# =========================
import os          # File paths, environment variables
import json        # Serialize / deserialize data
import hashlib     # Password hashing (SHA-256)
import subprocess  # Run Windows commands (icacls)

# =========================
# Third-party libraries
# =========================
from cryptography.fernet import Fernet  # Symmetric encryption (AES)
import win32crypt                      # Windows DPAPI (key protection)

# ======================================================
# Application identity (used for AppData folder name)
# ======================================================
APP_NAME = "Bloyckter"

# ======================================================
# AppData directory handling
# ======================================================
def get_app_data_dir():
    """
    Returns a secure, per-user application data directory.

    On Windows this resolves to:
    C:\\Users\\<USERNAME>\\AppData\\Local\\Bloyckter\\

    Why AppData?
    - Hidden by default
    - Per-user isolation
    - Standard Windows practice
    - Used by Chrome, VS Code, Edge, etc.
    """

    # LOCALAPPDATA is preferred (Local, non-roaming)
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")

    # Construct app-specific directory
    app_dir = os.path.join(base, APP_NAME)

    # Ensure directory exists
    os.makedirs(app_dir, exist_ok=True)

    return app_dir


# ======================================================
# File paths (centralized, single source of truth)
# ======================================================
APP_DATA_DIR = get_app_data_dir()

# Encrypted application data
DATA_FILE = os.path.join(APP_DATA_DIR, "data.enc")

# DPAPI-protected encryption key
KEY_FILE = os.path.join(APP_DATA_DIR, "key.blob")


# ======================================================
# NTFS permission hardening
# ======================================================
def restrict_permission(path: str):
    """
    Restrict file permissions so ONLY the current Windows user
    can access the file.

    This uses the Windows `icacls` command.

    Result:
    - Removes inherited permissions
    - Grants Full Control ONLY to current user
    - Other local users are denied access

    NOTE:
    - Admin users can still override (this is normal)
    - This raises the bar significantly for casual attacks
    """

    subprocess.run(
        f'icacls "{path}" /inheritance:r /grant:r %username%:F',
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# ======================================================
# DPAPI key management
# ======================================================
def load_key():
    """
    Loads or creates an AES encryption key protected by Windows DPAPI.

    SECURITY MODEL:
    - Key is NEVER stored in plaintext
    - Key is encrypted by Windows itself
    - Key is bound to:
        - Current Windows user
        - Current machine

    If files are copied elsewhere → decryption FAILS safely.
    """

    # --------------------------------------------------
    # First run: key does NOT exist
    # --------------------------------------------------
    if not os.path.exists(KEY_FILE):

        # Generate a new Fernet (AES) key
        key = Fernet.generate_key()

        # Protect the key using Windows DPAPI
        # Only this user on this machine can unprotect it
        # Use DPAPI to protect the key. PyWin32 expects up to 5 args
        # (data, description, optionalEntropy, promptStruct, flags).
        # Older code passed an extra reserved parameter which causes
        # a TypeError on some pywin32 versions.
        protected = win32crypt.CryptProtectData(
            key,
            None,
            None,
            None,
            0
        )

        # Save protected key to disk
        with open(KEY_FILE, "wb") as f:
            f.write(protected)

        # Lock down file permissions
        restrict_permission(KEY_FILE)

        return key

    # --------------------------------------------------
    # Key already exists → load & unprotect
    # --------------------------------------------------
    with open(KEY_FILE, "rb") as f:
        protected = f.read()

    # Unprotect key using Windows DPAPI
    # Call CryptUnprotectData with the supported arguments list.
    # The function returns a tuple where index 1 is the unprotected bytes.
    key = win32crypt.CryptUnprotectData(
        protected,
        None,
        None,
        None,
        0
    )[1]

    return key


# ======================================================
# Cipher creation (single responsibility)
# ======================================================
def get_cipher():
    """
    Returns a Fernet cipher object initialized with
    the DPAPI-protected AES key.

    This function hides ALL key-management details
    from the rest of the application.
    """
    return Fernet(load_key())


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
        cipher = get_cipher()

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

    cipher = get_cipher()

    # Serialize → bytes
    raw = json.dumps(data).encode()

    # Encrypt
    encrypted = cipher.encrypt(raw)

    # Write to disk
    with open(DATA_FILE, "wb") as f:
        f.write(encrypted)

    # Lock down permissions
    restrict_permission(DATA_FILE)


# ======================================================
# Password hashing
# ======================================================
def hash_password(password: str) -> str:
    """
    Hashes a password using SHA-256.

    WHY hashing?
    - Passwords are NEVER stored in plaintext
    - Even if data is decrypted, passwords are not revealed

    NOTE:
    - SHA-256 is acceptable for this project
    - Future upgrade path: bcrypt / argon2
    """
    return hashlib.sha256(password.encode()).hexdigest()
