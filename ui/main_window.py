import os
import csv
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QFileDialog, QMenu, QAbstractItemView)
from PySide6.QtGui import QAction
from ui.add_edit_dialog import AddEditDialog
from database import DatabaseManager
from cache import CacheManager
from generator import PasswordGenerator

class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager, cache: CacheManager, sync_key: bytes):
        super().__init__()
        self.db = db
        self.cache = cache
        self.sync_key = sync_key
        self.records = []
        self.setWindowTitle("Менеджер паролей")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.on_search)
        top_layout.addWidget(self.search_input)

        btn_add = QPushButton("+")
        btn_add.setFixedWidth(30)
        btn_add.clicked.connect(self.add_record)
        top_layout.addWidget(btn_add)

        btn_import = QPushButton("↓")
        btn_import.setFixedWidth(30)
        btn_import.clicked.connect(self.import_csv)
        top_layout.addWidget(btn_import)

        btn_export = QPushButton("↑")
        btn_export.setFixedWidth(30)
        btn_export.clicked.connect(self.export_csv)
        top_layout.addWidget(btn_export)

        btn_logout = QPushButton("Выйти")
        btn_logout.clicked.connect(self.logout)
        top_layout.addWidget(btn_logout)

        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Сервис", "Логин", "Почта", "Пароль"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.itemDoubleClicked.connect(self.edit_record)
        layout.addWidget(self.table)

        self.refresh_table()

    def refresh_table(self, records=None):
        if records is None:
            records = self.db.get_all_records(self.sync_key)
            self.records = records
        self.table.setRowCount(len(records))
        for i, rec in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(rec['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(rec['title']))
            self.table.setItem(i, 2, QTableWidgetItem(rec['service']))
            self.table.setItem(i, 3, QTableWidgetItem(rec['login']))
            self.table.setItem(i, 4, QTableWidgetItem(rec['email']))
            self.table.setItem(i, 5, QTableWidgetItem(rec['password']))
        self.table.hideColumn(0)

    def on_search(self, text):
        if not text.strip():
            self.refresh_table()
            return
        q = text.lower()
        filtered = [r for r in self.records if (
            q in r['title'].lower() or
            q in r['service'].lower() or
            q in r['login'].lower() or
            q in r['email'].lower() or
            q in r['password'].lower()
        )]
        self.refresh_table(filtered)

    def add_record(self):
        dialog = AddEditDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.db.add_record(
                data['title'], data['service'], data['login'],
                data['email'], data['password'], self.sync_key
            )
            self.refresh_table()

    def edit_record(self, item):
        row = item.row()
        record_id = int(self.table.item(row, 0).text())
        rec = next((r for r in self.records if r['id'] == record_id), None)
        if not rec:
            return
        dialog = AddEditDialog(self, rec)
        if dialog.exec():
            data = dialog.get_data()
            self.db.update_record(
                record_id,
                data['title'], data['service'], data['login'],
                data['email'], data['password'], self.sync_key
            )
            self.refresh_table()

    def delete_record(self, record_id):
        reply = QMessageBox.question(self, "Удаление", "Удалить запись?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_record(record_id)
            self.refresh_table()

    def show_context_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return
        record_id = int(self.table.item(row, 0).text())
        menu = QMenu()
        action_edit = QAction("Редактировать", self)
        action_edit.triggered.connect(lambda: self.edit_record(self.table.currentItem()))
        action_delete = QAction("Удалить", self)
        action_delete.triggered.connect(lambda: self.delete_record(record_id))
        menu.addAction(action_edit)
        menu.addAction(action_delete)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV файл", "",
                                                   "CSV файлы (*.csv);;Все файлы (*)")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                if not fieldnames:
                    QMessageBox.warning(self, "Ошибка", "Файл пуст или неверный формат")
                    return
                col_map = {}
                for col in fieldnames:
                    col_low = col.lower()
                    if 'title' in col_low or 'name' in col_low:
                        col_map['title'] = col
                    elif 'service' in col_low or 'site' in col_low:
                        col_map['service'] = col
                    elif 'login' in col_low or 'user' in col_low:
                        col_map['login'] = col
                    elif 'email' in col_low:
                        col_map['email'] = col
                    elif 'password' in col_low or 'pass' in col_low:
                        col_map['password'] = col
                if 'title' not in col_map or 'password' not in col_map:
                    QMessageBox.warning(self, "Ошибка", "Не найдены обязательные колонки: title и password")
                    return
                count = 0
                for row in reader:
                    title = row.get(col_map.get('title', ''), '').strip()
                    if not title:
                        continue
                    service = row.get(col_map.get('service', ''), '').strip()
                    login = row.get(col_map.get('login', ''), '').strip()
                    email = row.get(col_map.get('email', ''), '').strip()
                    password = row.get(col_map.get('password', ''), '').strip()
                    self.db.add_record(title, service, login, email, password, self.sync_key)
                    count += 1
                self.refresh_table()
                QMessageBox.information(self, "Импорт", f"Импортировано {count} записей.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать: {str(e)}")

    def export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "passwords.csv",
                                                   "CSV файлы (*.csv);;Все файлы (*)")
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Title", "Service", "Login", "Email", "Password"])
                for rec in self.records:
                    writer.writerow([rec['title'], rec['service'], rec['login'],
                                     rec['email'], rec['password']])
            QMessageBox.information(self, "Экспорт", f"Экспортировано {len(self.records)} записей.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать: {str(e)}")

    def logout(self):
        self.cache.delete_key()
        self.close()