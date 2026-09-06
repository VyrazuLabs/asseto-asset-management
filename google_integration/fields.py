from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


def _cipher() -> Fernet:
    """Build the Fernet cipher used to encrypt/decrypt DB-stored secrets.

    Returns:
        A Fernet instance keyed from `settings.FERNET_KEY`.

    Raises:
        ValueError: If `FERNET_KEY` is not configured — this must fail loudly
            rather than silently store plaintext.
    """
    key = getattr(settings, "FERNET_KEY", None)
    if not key:
        raise ValueError(
            "FERNET_KEY is not configured — required to store encrypted "
            "Google Cloud/Firebase credentials."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


class EncryptedTextField(models.TextField):
    """A TextField that transparently Fernet-encrypts values at rest.

    Plaintext is only ever held in memory; the DB column always stores the
    Fernet-encrypted token. This is the one real encrypted-field pattern in
    the codebase — existing per-user secrets (`configurations.SlackConfiguration`)
    use base64, which is encoding, not encryption, and is not reused here.
    """

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        return _cipher().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        return _cipher().decrypt(value.encode()).decode()
