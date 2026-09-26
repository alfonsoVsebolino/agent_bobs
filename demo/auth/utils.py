import hashlib
import re


def hash_password(password: str) -> str:
    """Return the SHA-256 hex digest of *password*."""
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Return True if *email* looks like a valid address, False otherwise."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))
