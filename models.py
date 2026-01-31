from dataclasses import dataclass
import time

@dataclass
class FolderLock:
    path: str
    password_hash: str
    max_attempts: int
    wait_time: int
    attempts: int = 0
    locked_until: float = 0.0

    def is_locked_out(self) -> bool:
        return time.time() < self.locked_until
    
    def remaining_wait(self) -> int:
        return max(0, int(self.locked_until - time.time()))