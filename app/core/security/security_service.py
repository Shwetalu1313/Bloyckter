import time
from app.data.repository import save_data

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
        
        # Persist the updated state to the encrypted database
        data[path] = info.__dict__
        save_data(data)
        
        return False, msg