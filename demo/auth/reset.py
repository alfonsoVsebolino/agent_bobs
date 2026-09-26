import secrets
from auth.user import get_user


def request_reset(user_id: str) -> str | None:
    """Return a reset token for *user_id*, or None if the user does not exist."""
    user = get_user(user_id)
    if user is None:
        return None
    return secrets.token_hex(16)
