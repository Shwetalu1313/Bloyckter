import os
import time
from app.core.hashing.pbkdf2 import hash_password
from app.data.repository import load_data, save_data
from app.data.models import FolderLock
from config import LOCK_SUFFIX
from .base import Protector
from app.core.security.security_service import SecurityService

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
            # Rename the cover nmae (obfuscation)
            os.rename(folder.path, locked_path)

            if folder.is_invisible:
                # Apply System and Hidden attributes on Windows
                os.system(f'attrib +h +s "{locked_path}"')
                
            else:
                # Leave it visible but renamed (Hint Mode)
                # We still apply +h (Hidden) so it's not immediately obvious,
                # but NOT +s (System), so "Hidden Items" will reveal it.
                os.system(f'attrib +h "{locked_path}"')

            SecurityService.hard_restrict_permission(locked_path) # Extra permission hardening for invisible folders
                

        except Exception as e:
            return False, f"Locking failed: {e}"
        
        # Update metadata with the new locked path and timestamp
        folder.locked_path = locked_path
        folder.locked_at = time.time()
        data[folder.path] = folder.__dict__
        
        save_data(data)
        return True, f"Folder secured as '{folder.cover_name}'."


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