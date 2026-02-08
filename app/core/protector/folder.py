import os
import time
import shutil
from app.core.hashing.pbkdf2 import hash_password
from app.data.repository import load_data, save_data
from app.data.models import FolderLock
from config import LOCK_SUFFIX
from .base import Protector
from app.core.security.security_service import SecurityService
from .archive import ArchiveProtector   

class FolderProtector(Protector):
    """
    Concrete implementation of Protector for local NTFS folders.
    Implements obfuscation via cover names and Windows attributes.
    """

    def lock(self, folder: FolderLock) -> tuple[bool, str]:
        data = load_data()

        if folder.path in data:
            return False, "Folder already managed."
        
        if not os.path.exists(folder.path):
            return False, "Target folder does not exist."
        
        # Determine the parent directory and build the obfuscated path
        parent_dir = os.path.dirname(folder.path)
        locked_path = os.path.join(parent_dir, folder.cover_name)

        if os.path.exists(locked_path):
            return False, "Cover name already exists. Choose a different one."
        
        try:
            # 1. ALWAYS Encrypt into a .bloyck archive
            # This turns the folder into a file that Windows Registry can track
            success, msg = ArchiveProtector().lock(folder)
            if not success:
                return False, msg
            
            # The folder is now deleted and replaced by a file at folder.locked_path
            locked_path = folder.locked_path

            if folder.is_invisible:
                # Stealth Mode: Hide it completely from Explorer
                os.system(f'attrib +h +s "{locked_path}"') 
            else:
                # Hint Mode: Keep it visible, but it's now a .bloyck file
                # It looks like a file, but double-clicking it opens your password box
                os.system(f'attrib +h "{locked_path}"') # Optional: Keep it slightly hidden

            # 2. Permission Lockdown
            # We use 'restrict' (not 'hard_restrict') so the app can read the file 
            # to verify the password when the user double-clicks it
            SecurityService.restrict_permission(locked_path)

        except Exception as e:
            return False, f"Locking failed: {e}"

        # Update metadata for the database
        folder.locked_path = locked_path
        folder.locked_at = time.time()
        data[folder.path] = folder.__dict__
        save_data(data)
        
        return True, f"Folder secured as '{folder.cover_name}.bloyck'."


    def unlock(self, target_path: str, password: str) -> tuple[bool, str]:
        data = load_data()
        if target_path not in data:
            return False, "Folder not found in vault."
        
        info = FolderLock(**data[target_path])

        if info.is_locked_out():
            return False, f"Security lockout: Wait {info.remaining_wait()}s."
        
        test_hash, _ = hash_password(password, info.password_salt)
        
        if test_hash == info.password_hash:
            try:
                SecurityService.restore_hard_permissions(info.locked_path)

                # Check for the correct extension (.bloyck, not .zip)
                if info.locked_path.lower().endswith('.bloyck'):
                    # Call the specialized decryptor
                    success, msg = ArchiveProtector().unlock(info.locked_path, password)
                    if not success:
                        return False, msg
                else:
                    # Handle normal obfuscated folders
                    os.system(f'attrib -h -s "{info.locked_path}"')
                    os.rename(info.locked_path, info.path)

                del data[target_path]
                save_data(data)
                return True, "Vault opened!"
            except Exception as e:
                return False, f"Restoration failed: {e}"
        
        # DELEGATION: Let the SecurityService handle the failure
        return SecurityService.handle_failed_attempt(target_path, info, data)

    def change_password(self, target_path: str, current_pwd: str, new_pwd: str) -> tuple[bool, str]:
        data = load_data()
        if target_path not in data:
            return False, "Folder not managed"
        
        info = FolderLock(**data[target_path])

        if info.is_locked_out():
            return False, f"Wait {info.remaining_wait()} seconds."

        test_hash, _ = hash_password(current_pwd, info.password_salt)
        
        if test_hash != info.password_hash:
            # DELEGATION: Use the same security rules for password changes
            return SecurityService.handle_failed_attempt(target_path, info, data)
        
        # Success logic...
        new_hash, new_salt = hash_password(new_pwd)
        info.password_hash = new_hash
        info.password_salt = new_salt
        info.attempts = 0
        info.locked_until = 0

        data[target_path] = info.__dict__
        save_data(data)
        return True, "Password updated successfully."