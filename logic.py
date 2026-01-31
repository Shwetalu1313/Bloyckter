import os
import time
from helper import load_data, save_data, hash_password
from models import FolderLock

LOCK_SUFFIX = "_LOCKED"

# LOCK FOLDER
def lock_folder(folder: FolderLock):
    
    # loading data
    data = load_data()

    if folder.path in data:
        return False, "Folder already managed"
    
    if not os.path.exists(folder.path):
        return False, "Folder doesn't exist"
    
    locked_path = folder.path + LOCK_SUFFIX

    try:
        os.rename(folder.path, locked_path)
        os.system(f'attrib +h +s "{locked_path}"')
    except Exception as e:
        return False, f"Locked Failed: {e}"
    
    data[folder.path] = folder.__dict__
    save_data(data)

    return True, "Folder locked successfully"

# UNLOCK FOLDER
def unlock_folder(folder_path: str, password: str):
    
    # loading data
    data = load_data()

    if folder_path not in data:
        return False, "Folder not managed"
    
    info = FolderLock(**data[folder_path])

    if info.is_locked_out():
        return False, f"Wait {info.remaining_wait()} seconds."
    
    if hash_password(password) == info.password_hash:
        locked_path = folder_path + LOCK_SUFFIX

        os.system(f'attrib -h -s "{locked_path}"')
        os.rename(locked_path, folder_path)

        del data[folder_path]
        save_data(data)

        return True, "Folder unlocked!"
    

    # wrong password

    info.attempts += 1

    if info.attempts >= info.max_attempts:
        info.locked_until = time.time() + info.wait_time()

        info.attempts = 0

    data[folder_path] = info.__dict__
    save_data(data)

    return False, "Wrong Password"


    

