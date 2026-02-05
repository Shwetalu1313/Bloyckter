import os

# Application Identity
APP_NAME = "Bloyckter"

# Security Constants
HASH_ITERATIONS = 100000
LOCK_SUFFIX = "_LOCKED"

# File System Paths
def get_app_data_dir():
    """Resolves the local AppData directory for the current user."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    app_dir = os.path.join(base, APP_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

APP_DATA_DIR = get_app_data_dir()
DATA_FILE = os.path.join(APP_DATA_DIR, "data.enc")
KEY_FILE = os.path.join(APP_DATA_DIR, "key.blob")