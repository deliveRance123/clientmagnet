import pytest
from app.core.encryption import encrypt_credential, decrypt_credential


def test_credential_encryption_decryption_roundtrip():
    plain_text = "my-secret-oauth-access-token-12345"
    cipher_text = encrypt_credential(plain_text)
    
    assert cipher_text is not None
    assert cipher_text != plain_text
    
    decrypted = decrypt_credential(cipher_text)
    assert decrypted == plain_text


def test_encryption_null_and_empty_handles():
    # Null values should return null
    assert encrypt_credential(None) is None
    assert decrypt_credential(None) is None
    
    # Empty string should return empty string
    assert encrypt_credential("") == ""
    assert decrypt_credential("") == ""


def test_decryption_invalid_ciphertext():
    with pytest.raises(ValueError):
        decrypt_credential("invalid-non-base64-ciphertext")
