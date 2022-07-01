import secrets
import string


def generate_password():
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(
        secrets.choice(alphabet) for _ in range(secrets.SystemRandom().randint(20, 30))
    )
    return password
