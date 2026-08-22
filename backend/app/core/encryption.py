import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

logger = logging.getLogger("app.encryption")

_key = settings.ENCRYPTION_KEY.encode()

try:
    _fernet = Fernet(_key)
except Exception as e:
    logger.warning(
        f"Failed to initialize Fernet with ENCRYPTION_KEY. Generating ephemeral key for safety. Error: {e}"
    )
    _fernet = Fernet(Fernet.generate_key())


def encrypt_credential(plain_text: Optional[str]) -> Optional[str]:
    """Encrypt a plaintext credential string using Fernet AES-256."""
    if plain_text is None:
        return None
    if not plain_text:
        return ""
    try:
        token = _fernet.encrypt(plain_text.encode("utf-8"))
        return token.decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError(f"Encryption failed: {str(e)}")


def decrypt_credential(cipher_text: Optional[str]) -> Optional[str]:
    """Decrypt a Fernet cipher text back to plaintext."""
    if cipher_text is None:
        return None
    if not cipher_text:
        return ""
    try:
        decrypted = _fernet.decrypt(cipher_text.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken:
        logger.error("Decryption failed: Invalid token or incorrect key.")
        raise ValueError("Decryption failed: Invalid token or incorrect key.")
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError(f"Decryption failed: {str(e)}")
