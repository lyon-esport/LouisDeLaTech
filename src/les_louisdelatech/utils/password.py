import hashlib
import secrets
import string


def generate_password() -> str:
    """Generate a strong but copy/paste-friendly password.

    We intentionally use only [A-Za-z0-9] to avoid:
    - non-printable characters (newline, tabs, etc.)
    - characters that can be visually confusing in support contexts
    - Discord/Markdown escaping issues when included in messages/templates
    """
    alphabet = string.ascii_letters + string.digits
    length = secrets.SystemRandom().randint(20, 30)
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str) -> str:
    """Return a SHA-1 hex digest (used by Google Admin API when hashFunction=SHA-1)."""
    return hashlib.sha1(password.encode()).hexdigest()
