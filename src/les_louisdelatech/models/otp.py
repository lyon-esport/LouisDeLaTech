from enum import StrEnum

from tortoise import fields
from tortoise.models import Model


class Digest(StrEnum):
    """Allowed digest algorithms for TOTP."""

    sha1 = "sha1"
    sha256 = "sha256"
    sha512 = "sha512"


class Otp(Model):
    """OTP secret storage (per team).

    Secrets are stored encrypted (Fernet) in SQLite via Tortoise ORM. The bot
    decrypts them at runtime to generate a TOTP code (pyotp).
    """

    name = fields.TextField(pk=True)
    team = fields.TextField()
    digest: Digest = fields.CharEnumField(Digest, default=Digest.sha1)
    digits = fields.SmallIntField(default=6)
    secret = fields.BinaryField()

    def __str__(self):
        return self.name
