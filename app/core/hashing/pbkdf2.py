import hashlib     # Password hashing (SHA-256)
import secrets     # secure random for salt generation
from config import HASH_ITERATIONS

# ======================================================
# Password hashing
# ======================================================
def hash_password(password: str, salt: str = None) -> tuple:
    """
    Securely hashes a password using PBKDF2-HMAC-SHA256.
    
    Args:
        password: The plaintext password.
        salt: Hex string salt. If None, a new 16-byte salt is generated.
        
    Returns:
        tuple: (hex_hash, hex_salt)
    """
    if salt is None:
        # Generate a secure 16-byte salt
        salt_bytes = secrets.token_bytes(16)
    else:
        salt_bytes = bytes.fromhex(salt)

    # PBKDF2 stretching
    # 100,000 iterations makes brute force significantly slower
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        HASH_ITERATIONS 
    )
    
    return key.hex(), salt_bytes.hex()