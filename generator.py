import secrets
import string
import re

class PasswordGenerator:
    def __init__(self, length=16):
        self.length = length
        self.chars = string.ascii_letters + string.digits + string.punctuation

    def generate(self) -> str:
        while True:
            pwd = ''.join(secrets.choice(self.chars) for _ in range(self.length))
            if self.validate(pwd):
                return pwd

    @staticmethod
    def validate(password: str) -> bool:
        if len(password) < 8:
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        if not re.search(r'[' + re.escape(string.punctuation) + r']', password):
            return False
        return True