import secrets
import string
from hashlib import pbkdf2_hmac


def generate_password():
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(
        secrets.choice(alphabet) for _ in range(secrets.SystemRandom().randint(20, 30))
    )
    return password


def hash_password(password, salt):
    our_app_iters = 500_000  # Application specific, read above.
    dk = pbkdf2_hmac("sha512", password, salt, our_app_iters)
    return dk.hex()