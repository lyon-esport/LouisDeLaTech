import hashlib
import secrets


def generate_password() -> str:
    ascii_alphabet = "".join(chr(i) for i in range(128))
    password = "".join(
        secrets.choice(ascii_alphabet)
        for _ in range(secrets.SystemRandom().randint(20, 30))
    )
    return password


def hash_password(password: str) -> str:
    return hashlib.sha1(password.encode()).hexdigest()
