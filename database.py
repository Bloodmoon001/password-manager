import sqlite3
import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str, crypto):
        self.db_path = db_path
        self.crypto = crypto
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash BLOB NOT NULL,
                    salt BLOB NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    service_enc BLOB,
                    login_enc BLOB,
                    email_enc BLOB,
                    password_enc BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def register_user(self, username: str, password: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users LIMIT 1")
            if cur.fetchone():
                return False
            salt, pwd_hash = self.crypto.hash_password(password)
            cur.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, pwd_hash, salt)
            )
            conn.commit()
            return True

    def authenticate_user(self, username: str, password: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if not row:
                return False
            stored_hash, salt = row
            return self.crypto.verify_password(password, salt, stored_hash)

    def _encrypt_field(self, value: str, key: bytes) -> bytes:
        if not value:
            return b''
        return self.crypto.encrypt_aes(value.encode('utf-8'), key)

    def _decrypt_field(self, encrypted: bytes, key: bytes) -> str:
        if not encrypted:
            return ''
        return self.crypto.decrypt_aes(encrypted, key).decode('utf-8')

    def add_record(self, title: str, service: str, login: str, email: str, password: str, key: bytes):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO passwords (title, service_enc, login_enc, email_enc, password_enc)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                title,
                self._encrypt_field(service, key),
                self._encrypt_field(login, key),
                self._encrypt_field(email, key),
                self._encrypt_field(password, key)
            ))
            conn.commit()

    def get_all_records(self, key: bytes) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT id, title, service_enc, login_enc, email_enc, password_enc, created_at
                FROM passwords ORDER BY created_at DESC
            ''')
            rows = cur.fetchall()
        records = []
        for row in rows:
            records.append({
                'id': row[0],
                'title': row[1],
                'service': self._decrypt_field(row[2], key),
                'login': self._decrypt_field(row[3], key),
                'email': self._decrypt_field(row[4], key),
                'password': self._decrypt_field(row[5], key),
                'created_at': row[6]
            })
        return records

    def update_record(self, record_id: int, title: str, service: str, login: str, email: str, password: str, key: bytes):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''
                UPDATE passwords
                SET title=?, service_enc=?, login_enc=?, email_enc=?, password_enc=?
                WHERE id=?
            ''', (
                title,
                self._encrypt_field(service, key),
                self._encrypt_field(login, key),
                self._encrypt_field(email, key),
                self._encrypt_field(password, key),
                record_id
            ))
            conn.commit()

    def delete_record(self, record_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM passwords WHERE id=?", (record_id,))
            conn.commit()

    def search_records(self, query: str, key: bytes) -> List[Dict]:
        all_records = self.get_all_records(key)
        if not query:
            return all_records
        q = query.lower()
        result = []
        for rec in all_records:
            if (q in rec['title'].lower() or
                q in rec['service'].lower() or
                q in rec['login'].lower() or
                q in rec['email'].lower() or
                q in rec['password'].lower()):
                result.append(rec)
        return result