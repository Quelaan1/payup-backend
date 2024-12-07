from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64


def encrypt_entity_id(entity_id: str, key: str) -> str:
    """Encrypt the entity ID using AES"""
    key_bytes = base64.b64decode(key)  # Decode the base64-encoded key
    iv = b"\0" * 16  # Use a fixed 16-byte IV (all zeros)
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padded_entity_id = entity_id.encode().rjust(
        16, b"\0"
    )  # Pad the entity_id to 16 bytes
    encrypted_entity_id = encryptor.update(padded_entity_id) + encryptor.finalize()
    return base64.b64encode(encrypted_entity_id).decode()


def decrypt_entity_id(encrypted_entity_id: str, key: str) -> str:
    """Decrypt the encrypted entity ID using AES"""
    key_bytes = base64.b64decode(key)  # Decode the base64-encoded key
    encrypted_entity_id_bytes = base64.b64decode(
        encrypted_entity_id
    )  # Decode the base64-encoded encrypted entity ID
    iv = b"\0" * 16  # Use the same fixed 16-byte IV (all zeros)
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_entity_id = (
        decryptor.update(encrypted_entity_id_bytes) + decryptor.finalize()
    )
    return decrypted_entity_id.strip(b"\0").decode()
