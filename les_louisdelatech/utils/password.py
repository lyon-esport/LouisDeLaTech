import crypt
import secrets
import string


def generate_password():
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(
        secrets.choice(alphabet) for _ in range(secrets.SystemRandom().randint(20, 30))
    )
    return password


def hash_password(password: str):
    return crypt.crypt(password, crypt.METHOD_SHA512)
