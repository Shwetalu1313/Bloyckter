import time
import subprocess                      # Run Windows commands (icacls)

class SecurityService:
    """
    Manages security rules including failed attempts, 
    lockout durations, and state persistence.
    """

    @staticmethod
    def handle_failed_attempt(path: str, info, data: dict) -> tuple[bool, str]:
        """
        Increments attempts and sets lockout timestamp if threshold is reached.
       
        """
        info.attempts += 1
        
        if info.attempts >= info.max_attempts:
            # Set the lockout expiration time
            info.locked_until = time.time() + info.wait_time
            info.attempts = 0 # Reset counter for the next window
            
            msg = (
                f"Too many wrong attempts.\n"
                f"Locked for {info.wait_time} seconds."
            )
        else:
            msg = f"Invalid password. {info.max_attempts - info.attempts} tries left."
        
        # Persist the updated state to the encrypted database.
        # Import `save_data` here to avoid a circular import at module import time
        # (app.data.repository imports dpapi which imports this module).
        from app.data.repository import save_data

        data[path] = info.__dict__
        save_data(data)
        
        return False, msg
    
    @staticmethod
    # ======================================================
    # NTFS permission hardening for windows users
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

    @staticmethod
    def hard_restrict_permission(path: str):
        """
        An even more aggressive permission hardening that also
        denies access to the SYSTEM user.

        WARNING:
        - This can cause issues with some backup software or system processes.
        - Use with caution and test on non-critical files first.
        """

        # NEW: Lockdown permissions so NO ONE can open it
        # This removes all permissions and denies access to the folder contents
        subprocess.run(
            f'icacls "{path}" /inheritance:r /deny *S-1-1-0:(OI)(CI)(F)', 
            shell=True, stdout=subprocess.DEVNULL
        )
        # *S-1-1-0 is the SID for "Everyone" in Windows.

    @staticmethod
    def restore_hard_permissions(path: str):
        """
        Restores permissions to allow access again.
        This is necessary before deleting or modifying the file.
        """

        # NEW: Restore permissions before trying to rename
        subprocess.run(
            f'icacls "{path}" /grant *S-1-1-0:(OI)(CI)(F)', 
            shell=True, stdout=subprocess.DEVNULL
        )