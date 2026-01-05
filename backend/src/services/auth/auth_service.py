"""Authentication service for password hashing and verification."""
import hashlib
import bcrypt
from src.utils.logger import get_logger

logger = get_logger("auth_service")

# Bcrypt rounds
BCRYPT_ROUNDS = 12


def _preprocess_password(password: str) -> bytes:
    """
    Preprocess password with SHA-256 to handle passwords longer than 72 bytes.
    This allows bcrypt to handle arbitrary length passwords while maintaining security.
    Returns bytes (32 bytes) which is always < 72 bytes.
    """
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Preprocess with SHA-256 to handle passwords longer than bcrypt's 72-byte limit
    # SHA-256 digest is always 32 bytes, which is safe
    preprocessed = _preprocess_password(password)
    # Hash with bcrypt
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    password_hash = bcrypt.hashpw(preprocessed, salt)
    # Return as string (decode from bytes)
    return password_hash.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        # Preprocess with SHA-256 to match the hashing process
        preprocessed = _preprocess_password(plain_password)
        # Verify with bcrypt
        # Encode hashed_password to bytes if it's a string
        if isinstance(hashed_password, str):
            hashed_password_bytes = hashed_password.encode("utf-8")
        else:
            hashed_password_bytes = hashed_password
        return bcrypt.checkpw(preprocessed, hashed_password_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

