
import sys
import winreg
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QComboBox, QLineEdit,
    QFormLayout, QDialog, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt

class EditDialog(QDialog):
    def __init__(self, name, command, icon, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Context Menu Item")
        layout = QFormLayout()

        self.name_edit = QLineEdit(name)
        self.cmd_edit = QLineEdit(command)
        self.icon_edit = QLineEdit(icon)

        layout.addRow("Name:", self.name_edit)
        layout.addRow("Command:", self.cmd_edit)
        layout.addRow("Icon Path:", self.icon_edit)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.setLayout(layout)

    def get_values(self):
        return self.name_edit.text(), self.cmd_edit.text(), self.icon_edit.text()


class ContextMenuManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Context Menu Manager")
        self.setGeometry(200, 200, 700, 400)

        self.registry_paths = {
            "*": r"*\shell",
            "Directory": r"Directory\shell",
            "Directory Background": r"Directory\Background\shell",
            "Drive": r"Drive\shell"
        }

        layout = QVBoxLayout()
        dropdown_layout = QHBoxLayout()

        self.type_label = QLabel("Context Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.registry_paths.keys())
        self.type_combo.currentTextChanged.connect(self.load_context_menu)

        dropdown_layout.addWidget(self.type_label)
        dropdown_layout.addWidget(self.type_combo)
        layout.addLayout(dropdown_layout)

        self.menu_list = QListWidget()
        layout.addWidget(self.menu_list)

        button_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.up_btn = QPushButton("Up")
        self.down_btn = QPushButton("Down")
        self.refresh_btn = QPushButton("Refresh")

        self.edit_btn.clicked.connect(self.edit_item)
        self.delete_btn.clicked.connect(self.delete_item)
        self.up_btn.clicked.connect(self.move_up)
        self.down_btn.clicked.connect(self.move_down)
        self.refresh_btn.clicked.connect(self.load_context_menu)

        for btn in [self.edit_btn, self.delete_btn, self.up_btn, self.down_btn, self.refresh_btn]:
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.load_context_menu()

    def open_registry_key(self, path, access=winreg.KEY_READ):
        try:
            return winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path, 0, access)
        except FileNotFoundError:
            return None

    def load_context_menu(self):
        self.menu_list.clear()
        selected_type = self.type_combo.currentText()
        reg_path = self.registry_paths[selected_type]
        key = self.open_registry_key(reg_path)
        if key:
            i = 0
            while True:
                try:
                    subkey = winreg.EnumKey(key, i)
                    self.menu_list.addItem(subkey)
                    i += 1
                except OSError:
                    break

    def get_selected_item_info(self):
        selected_type = self.type_combo.currentText()
        reg_path = self.registry_paths[selected_type]
        item = self.menu_list.currentItem()
        if not item:
            return None, None
        item_name = item.text()
        key_path = f"{reg_path}\{item_name}"
        cmd = ""
        icon = ""

        try:
            with self.open_registry_key(key_path) as k:
                try:
                    icon = winreg.QueryValueEx(k, "Icon")[0]
                except FileNotFoundError:
                    pass

            with self.open_registry_key(f"{key_path}\command") as k:
                cmd = winreg.QueryValueEx(k, "")[0]
        except Exception:
            pass

        return item_name, (cmd, icon, key_path)

    def edit_item(self):
        item_name, info = self.get_selected_item_info()
        if not info:
            return
        cmd, icon, key_path = info
        dlg = EditDialog(item_name, cmd, icon, self)
        if dlg.exec_():
            new_name, new_cmd, new_icon = dlg.get_values()
            reg_path = self.registry_paths[self.type_combo.currentText()]
            old_key = f"{reg_path}\{item_name}"
            new_key = f"{reg_path}\{new_name}"

            try:
                # Rename if name changed
                if new_name != item_name:
                    winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, new_key)
                    # TODO: Copy all values from old_key to new_key (not implemented yet)
                    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, old_key)
                # Update command and icon
                winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, new_key)
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, new_key, 0, winreg.KEY_WRITE) as k:
                    winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, new_icon)
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{new_key}\command") as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, new_cmd)
                QMessageBox.information(self, "Success", f"Updated {new_name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
            self.load_context_menu()

    def delete_item(self):
        item = self.menu_list.currentItem()
        if not item:
            return
        name = item.text()
        reg_path = self.registry_paths[self.type_combo.currentText()]
        key_path = f"{reg_path}\{name}"
        try:
            # Delete command first
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\command")
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
            QMessageBox.information(self, "Deleted", f"Deleted {name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        self.load_context_menu()

    def move_up(self):
        row = self.menu_list.currentRow()
        if row > 0:
            item = self.menu_list.takeItem(row)
            self.menu_list.insertItem(row - 1, item)
            self.menu_list.setCurrentRow(row - 1)

    def move_down(self):
        row = self.menu_list.currentRow()
        if row < self.menu_list.count() - 1:
            item = self.menu_list.takeItem(row)
            self.menu_list.insertItem(row + 1, item)
            self.menu_list.setCurrentRow(row + 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ContextMenuManager()
    win.show()
    sys.exit(app.exec_())
