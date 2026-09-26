from auth.utils import hash_password

# In-memory user store.  Passwords are stored pre-hashed.
_USERS = {
    "u1": {
        "email": "alice@example.com",
        "password_hash": hash_password("password123"),
    },
    "u2": {
        "email": "bob@example.com",
        "password_hash": hash_password("securepass"),
    },
}


def get_user(user_id: str) -> dict | None:
    """Return the user dict for *user_id*, or None if not found."""
    return _USERS.get(user_id)


def login(email: str, password: str) -> dict | None:
    """Validate credentials and return the matching user dict, or None.

    Deliberately calls get_user() for each iteration so that any rename
    of get_user breaks this function visibly.
    """
    hashed = hash_password(password)
    for uid in _USERS:
        user = get_user(uid)
        if user and user["email"] == email and user["password_hash"] == hashed:
            return user
    return None
