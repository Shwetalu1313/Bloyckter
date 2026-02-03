import os
import time
from helper import load_data, save_data, hash_password
from models import FolderLock

LOCK_SUFFIX = "_LOCKED"

def lock_folder(folder: FolderLock):
    """
    Renames a folder and records its metadata with a unique salt.
    """
    data = load_data()

    if folder.path in data:
        return False, "Folder already managed."
    
    if not os.path.exists(folder.path):
        return False, "Target folder does not exist."
    
    locked_path = folder.path + LOCK_SUFFIX

    try:
        os.rename(folder.path, locked_path)
        # Apply System and Hidden attributes on Windows
        os.system(f'attrib +h +s "{locked_path}"')
    except Exception as e:
        return False, f"Locking failed: {e}"
    
    # Store the object including the salt
    folder.locked_path = locked_path
    folder.locked_at = time.time()
    data[folder.path] = folder.__dict__
    
    save_data(data)
    return True, "Folder secured successfully."

def unlock_folder(folder_path: str, password: str):
    """
    Verifies password using stored salt and restores folder if correct.
    """
    data = load_data()

    if folder_path not in data:
        return False, "Folder not found in vault."
    
    info = FolderLock(**data[folder_path])

    if info.is_locked_out():
        return False, f"Security lockout: Wait {info.remaining_wait()}s."
    
    # New Verification: Use the stored salt
    test_hash, _ = hash_password(password, info.password_salt)
    
    if test_hash == info.password_hash:
        try:
            os.system(f'attrib -h -s "{info.locked_path}"')
            os.rename(info.locked_path, info.path)
            del data[folder_path]
            save_data(data)
            return True, "Vault opened!"
        except Exception as e:
            return False, f"System error during restoration: {e}"
    
    # Handle failed attempt
    info.attempts += 1
    if info.attempts >= info.max_attempts:
        info.locked_until = time.time() + info.wait_time
        info.attempts = 0
        msg = f"Locked for {info.wait_time}s due to failed attempts."
    else:
        msg = f"Invalid password. {info.max_attempts - info.attempts} tries left."
    
    data[folder_path] = info.__dict__
    save_data(data)
    return False, msg

# managed folders
def get_managed_folders():
    data = load_data()
    return list(data.keys())

def change_password(folder_path: str, current_password: str, new_password: str):
    data = load_data()
    if folder_path not in data:
        return False, "Folder not managed"
    
    info = FolderLock(**data[folder_path])

    if info.is_locked_out():
        return False, f"Wait {info.remaining_wait()} seconds."

    # FIX: Must use stored salt to verify the current password!
    test_hash, _ = hash_password(current_password, info.password_salt)
    
    if test_hash != info.password_hash:
        info.attempts += 1
        
        #Trigger lockout if max attempts reached
        if info.attempts >= info.max_attempts:
            info.locked_until = time.time() + info.wait_time # lockout 
            info.attempts = 0 # reset attempts

            data[folder_path] = info.__dict__ # save changes on object
            save_data(data)

            return False, (
            f"Too many wrong attempts.\n"
            f"Locked for {info.wait_time} seconds."
            )

        data[folder_path] = info.__dict__
        save_data(data)
        return False, f"Wrong password. {info.max_attempts - info.attempts} left."
    
    # SUCCESS: Generate a FRESH salt for the new password (best practice)
    new_hash, new_salt = hash_password(new_password)
    
    info.password_hash = new_hash
    info.password_salt = new_salt
    info.attempts = 0
    info.locked_until = 0

    data[folder_path] = info.__dict__
    save_data(data)
    return True, "Password updated with new secure salt."