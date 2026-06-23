import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog, QLineEdit
from PySide6.QtCore import QTimer
from crypto import CryptoManager
from database import DatabaseManager
from cache import CacheManager
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "passwords.db")

    crypto = CryptoManager(data_dir)
    db = DatabaseManager(db_path, crypto)
    cache = CacheManager()

    if not crypto.keys_exist():
        username, ok = QInputDialog.getText(None, "Регистрация", "Введите имя пользователя:")
        if not ok or not username:
            sys.exit(0)
        password, ok = QInputDialog.getText(None, "Регистрация", "Введите мастер-пароль:",
                                            QLineEdit.Password)
        if not ok or not password:
            sys.exit(0)
        pwd2, ok = QInputDialog.getText(None, "Регистрация", "Повторите пароль:",
                                        QLineEdit.Password)
        if not ok or password != pwd2:
            QMessageBox.critical(None, "Ошибка", "Пароли не совпадают")
            sys.exit(1)

        if not db.register_user(username, password):
            QMessageBox.critical(None, "Ошибка", "Пользователь уже существует?")
            sys.exit(1)

        crypto.generate_async_keys(password)
        sync_key = crypto.generate_sync_key()
        crypto.encrypt_sync_key_with_rsa(sync_key)

        QMessageBox.information(None, "Успех", "Регистрация завершена. Ключи созданы.")

    username, ok = QInputDialog.getText(None, "Вход", "Введите имя пользователя:")
    if not ok or not username:
        sys.exit(0)
    password, ok = QInputDialog.getText(None, "Вход", "Введите мастер-пароль:",
                                        QLineEdit.Password)
    if not ok or not password:
        sys.exit(0)

    if not db.authenticate_user(username, password):
        QMessageBox.critical(None, "Ошибка", "Неверное имя или пароль")
        sys.exit(1)

    try:
        sync_key = crypto.decrypt_sync_key_with_rsa(password)
    except Exception:
        QMessageBox.critical(None, "Ошибка", "Не удалось расшифровать ключ. Проверьте пароль.")
        sys.exit(1)

    cache.set_key(sync_key)

    window = MainWindow(db, cache, sync_key)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()