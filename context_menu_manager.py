import sys
import winreg
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QComboBox, QInputDialog, QMessageBox
)

class ContextMenuManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Context Menu Manager")
        self.setGeometry(200, 200, 600, 400)

        self.registry_paths = {
            "*": r"*\shell",
            "Directory": r"Directory\shell",
            "Directory Background": r"Directory\Background\shell",
            "Drive": r"Drive\shell",
            "All File Types": r"*\shell",
        }

        layout = QVBoxLayout()
        dropdown_layout = QHBoxLayout()

        self.type_label = QLabel("Context Menu Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.registry_paths.keys())
        self.type_combo.currentTextChanged.connect(self.load_context_menu)

        dropdown_layout.addWidget(self.type_label)
        dropdown_layout.addWidget(self.type_combo)
        layout.addLayout(dropdown_layout)

        self.menu_list = QListWidget()
        layout.addWidget(self.menu_list)

        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.up_button = QPushButton("Up")
        self.down_button = QPushButton("Down")
        self.refresh_button = QPushButton("Refresh")

        self.edit_button.clicked.connect(self.edit_item)
        self.delete_button.clicked.connect(self.delete_item)
        self.up_button.clicked.connect(self.move_item_up)
        self.down_button.clicked.connect(self.move_item_down)
        self.refresh_button.clicked.connect(self.load_context_menu)

        for b in [self.edit_button, self.delete_button, self.up_button, self.down_button, self.refresh_button]:
            button_layout.addWidget(b)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.load_context_menu()

    def get_registry_key(self, key_path):
        try:
            return winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path)
        except FileNotFoundError:
            return None

    def load_context_menu(self):
        self.menu_list.clear()
        selected_type = self.type_combo.currentText()
        reg_path = self.registry_paths[selected_type]
        key = self.get_registry_key(reg_path)

        if key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    self.menu_list.addItem(subkey_name)
                    i += 1
                except OSError:
                    break

    def edit_item(self):
        current_item = self.menu_list.currentItem()
        if current_item:
            new_text, ok = QInputDialog.getText(self, "Edit Context Menu Item", "New name:", text=current_item.text())
            if ok:
                current_item.setText(new_text)
                # Registry rename logic coming next

    def delete_item(self):
        current_item = self.menu_list.currentItem()
        if current_item:
            QMessageBox.information(self, "Simulated", f"Would delete: {current_item.text()}")
            # Registry delete logic to be implemented

    def move_item_up(self):
        row = self.menu_list.currentRow()
        if row > 0:
            item = self.menu_list.takeItem(row)
            self.menu_list.insertItem(row - 1, item)
            self.menu_list.setCurrentRow(row - 1)

    def move_item_down(self):
        row = self.menu_list.currentRow()
        if row < self.menu_list.count() - 1:
            item = self.menu_list.takeItem(row)
            self.menu_list.insertItem(row + 1, item)
            self.menu_list.setCurrentRow(row + 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ContextMenuManager()
    window.show()
    sys.exit(app.exec_())
