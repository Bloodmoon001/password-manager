import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256

class CryptoManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.sync_key_path = os.path.join(data_dir, "sync_key.bin")
        self.async_public_path = os.path.join(data_dir, "rsa_public.pem")
        self.async_private_path = os.path.join(data_dir, "rsa_private.pem")

    def generate_sync_key(self):
        return get_random_bytes(32)

    def generate_async_keys(self, password):
        key = RSA.generate(2048)
        private_pem = key.export_key(
            format='PEM',
            passphrase=password,
            protection='PBKDF2WithHMAC-SHA512AndAES256-CBC',
            prot_params={'iteration_count': 1_000_000}
        )
        public_pem = key.public_key().export_key()
        with open(self.async_private_path, 'wb') as f:
            f.write(private_pem)
        with open(self.async_public_path, 'wb') as f:
            f.write(public_pem)

    def encrypt_sync_key_with_rsa(self, sync_key):
        with open(self.async_public_path, 'rb') as f:
            pub_key = RSA.import_key(f.read())
        cipher = PKCS1_OAEP.new(pub_key)
        encrypted = cipher.encrypt(sync_key)
        with open(self.sync_key_path, 'wb') as f:
            f.write(encrypted)

    def decrypt_sync_key_with_rsa(self, password):
        with open(self.async_private_path, 'rb') as f:
            private_key = RSA.import_key(f.read(), passphrase=password)
        with open(self.sync_key_path, 'rb') as f:
            encrypted = f.read()
        cipher = PKCS1_OAEP.new(private_key)
        sync_key = cipher.decrypt(encrypted)
        return sync_key

    def encrypt_aes(self, data: bytes, key: bytes) -> bytes:
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + tag + ciphertext

    def decrypt_aes(self, encrypted_data: bytes, key: bytes) -> bytes:
        nonce = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

    def hash_password(self, password: str, salt: bytes = None) -> tuple:
        if salt is None:
            salt = get_random_bytes(32)
        key = PBKDF2(password, salt, dkLen=32, count=100_000, hmac_hash_module=SHA256)
        return salt, key

    def verify_password(self, password: str, salt: bytes, stored_hash: bytes) -> bool:
        _, computed = self.hash_password(password, salt)
        return computed == stored_hash

    def keys_exist(self):
        return (os.path.exists(self.async_public_path) and
                os.path.exists(self.async_private_path) and
                os.path.exists(self.sync_key_path))