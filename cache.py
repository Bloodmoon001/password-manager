import keyring
import threading
import socket
import base64

class CacheManager:
    def __init__(self, service_name="PasswordManager"):
        self.service = service_name
        self.username = socket.gethostname()

    def set_key(self, key: bytes):
        key_b64 = base64.b64encode(key).decode('ascii')
        keyring.set_password(self.service, self.username, key_b64)

    def get_key(self) -> bytes:
        key_b64 = keyring.get_password(self.service, self.username)
        if key_b64:
            return base64.b64decode(key_b64)
        return None

    def delete_key(self):
        keyring.delete_password(self.service, self.username)

    def set_timer(self, delay_seconds: int, callback=None):
        def clear():
            self.delete_key()
            if callback:
                callback()
        timer = threading.Timer(delay_seconds, clear)
        timer.daemon = True
        timer.start()
        return timer