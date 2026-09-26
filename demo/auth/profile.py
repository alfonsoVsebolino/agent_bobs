from auth.user import get_user  # top-level import — rename breaks this line


def update_profile(user_id: str, name: str) -> dict | None:
    """Look up *user_id* via get_user and update the display name.

    Returns the updated user dict, or None if the user does not exist.
    """
    user = get_user(user_id)
    if user is None:
        return None
    user["name"] = name
    return user
