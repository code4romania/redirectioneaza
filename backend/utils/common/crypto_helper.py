from django.conf import settings


def encrypt_data(data: bytes) -> str:
    return settings.FERNET_OBJECT.encrypt(data).decode()


def decrypt_data(token: bytes) -> str:
    return settings.FERNET_OBJECT.decrypt(token).decode()
