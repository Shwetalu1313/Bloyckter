import win32crypt                      # Windows DPAPI (key protection)
import os                              # File paths
from cryptography.fernet import Fernet  # Symmetric encryption (AES)
from config import KEY_FILE
from app.core.security.security_service import SecurityService # For permission hardening

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
        # CryptProtectData signatures vary across pywin32 versions.
        # Try a few calling conventions for compatibility.
        try:
            # Preferred: explicit promptStruct=None, flags=0
            protected = win32crypt.CryptProtectData(
                key,
                None,
                None,
                None,
                None,
                0,
            )
        except TypeError:
            try:
                # Fallback: (data, description, optionalEntropy, promptStruct, flags)
                protected = win32crypt.CryptProtectData(
                    key,
                    None,
                    None,
                    None,
                    0,
                )
            except TypeError:
                # Minimal fallback: only data
                protected = win32crypt.CryptProtectData(key)

        # Save protected key to disk
        with open(KEY_FILE, "wb") as f:
            f.write(protected)

        # Lock down file permissions
        SecurityService.restrict_permission(KEY_FILE)
        return key

    # --------------------------------------------------
    # Key already exists → load & unprotect
    # --------------------------------------------------
    with open(KEY_FILE, "rb") as f:
        protected = f.read()

    # Unprotect key using Windows DPAPI
    # Call CryptUnprotectData with the supported arguments list.
    # The function returns a tuple where index 1 is the unprotected bytes.
    # CryptUnprotectData signatures vary; try compatible call patterns.
    try:
        key = win32crypt.CryptUnprotectData(
            protected,
            None,
            None,
            None,
            None,
            0,
        )[1]
    except TypeError:
        try:
            key = win32crypt.CryptUnprotectData(
                protected,
                None,
                None,
                None,
                0,
            )[1]
        except TypeError:
            key = win32crypt.CryptUnprotectData(protected)[1]

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

