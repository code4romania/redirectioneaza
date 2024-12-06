import hashlib

from django.conf import settings


def hash_id_secret(prefix: str, pk: int) -> str:
    return hashlib.blake2s(
        f"{prefix}-{pk}-{settings.SECRET_KEY_HASH}".encode(), digest_size=16, usedforsecurity=False
    ).hexdigest()
