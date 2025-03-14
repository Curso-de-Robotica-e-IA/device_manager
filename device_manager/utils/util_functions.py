import secrets
import string


def create_password(size: int = 8) -> str:
    """Creates a random password.
    The password contains only alphanumeric characters.

    Args:
        size (int, optional): The size of the password. Defaults to 8.

    Returns:
        str: The random password.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(size))
