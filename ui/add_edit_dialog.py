from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QPushButton, QHBoxLayout, QDialogButtonBox)
from generator import PasswordGenerator

class AddEditDialog(QDialog):
    def __init__(self, parent=None, record=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("Добавить запись" if record is None else "Редактировать запись")
        self.resize(500, 300)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.title_edit = QLineEdit()
        self.service_edit = QLineEdit()
        self.login_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        form.addRow("Название:", self.title_edit)
        form.addRow("Сервис:", self.service_edit)
        form.addRow("Логин:", self.login_edit)
        form.addRow("Почта:", self.email_edit)
        form.addRow("Пароль:", self.password_edit)

        gen_btn = QPushButton("Сгенерировать")
        gen_btn.clicked.connect(self.generate_password)
        form.addRow("", gen_btn)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if record:
            self.title_edit.setText(record['title'])
            self.service_edit.setText(record['service'])
            self.login_edit.setText(record['login'])
            self.email_edit.setText(record['email'])
            self.password_edit.setText(record['password'])

    def generate_password(self):
        gen = PasswordGenerator(length=16)
        pwd = gen.generate()
        self.password_edit.setText(pwd)

    def get_data(self):
        return {
            'title': self.title_edit.text().strip(),
            'service': self.service_edit.text().strip(),
            'login': self.login_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'password': self.password_edit.text().strip()
        }