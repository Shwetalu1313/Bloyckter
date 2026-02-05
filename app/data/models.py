from dataclasses import dataclass
import time

@dataclass
class FolderLock:

    """
    Data model for a locked folder.
    
    Attributes:
        path: Original absolute path to the folder.
        password_hash: PBKDF2 stretched hash of the password.
        password_salt: Unique random salt used for this specific folder.
        max_attempts: Number of failed tries allowed before lockout.
        wait_time: Seconds to wait during lockout.
        locked_path: The path of the folder once renamed/hidden.
    """

    path: str
    password_hash: str
    password_salt: str
    max_attempts: int
    wait_time: int
    cover_name: str
    attempts: int = 0
    locked_until: float = 0.0
    locked_at: float = 0.0
    locked_path: str = ""

    def is_locked_out(self) -> bool:
        """Returns True if the folder is currently in a cooldown state."""
        return time.time() < self.locked_until
    
    def remaining_wait(self) -> int:
        """Returns the integer seconds remaining in lockout."""
        return max(0, int(self.locked_until - time.time()))