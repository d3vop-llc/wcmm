import tkinter as tk
from tkinter import ttk, messagebox
import winreg

def list_file_types():
    types = []
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "") as key:
            i = 0
            while True:
                subkey = winreg.EnumKey(key, i)
                if subkey.startswith(".") or subkey in ("*", "Folder", "Directory", "Drive"):
                    types.append(subkey)
                i += 1
    except OSError:
        pass
    return sorted(set(types))

def get_shell_commands(file_type):
    commands = []

    try:
        # Step 1: Resolve file type association (e.g., .txt → txtfile)
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, file_type) as type_key:
            try:
                file_class, _ = winreg.QueryValueEx(type_key, "")
            except FileNotFoundError:
                file_class = None
    except FileNotFoundError:
        file_class = None

    # Step 2: Determine actual registry path to look under
    if file_class:
        target_key_path = f"{file_class}\\shell"
    else:
        target_key_path = f"{file_type}\\shell"

    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, target_key_path) as shell_key:
            i = 0
            while True:
                try:
                    entry = winreg.EnumKey(shell_key, i)
                    try:
                        with winreg.OpenKey(shell_key, fr"{entry}\command") as cmd_key:
                            command, _ = winreg.QueryValueEx(cmd_key, "")
                            commands.append(f"{entry} → {command}")
                    except FileNotFoundError:
                        commands.append(f"{entry} → [No command found]")
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        commands.append(f"[No shell entries under {target_key_path}]")

    return commands

def on_select(event):
    file_type = filetype_combo.get()
    command_list.delete(0, tk.END)
    for cmd in get_shell_commands(file_type):
        command_list.insert(tk.END, cmd)

root = tk.Tk()
root.title("Context Menu Manager")
root.geometry("700x400")

tk.Label(root, text="Select File Type:").pack(pady=5)

filetype_combo = ttk.Combobox(root, values=list_file_types(), width=50)
filetype_combo.pack()
filetype_combo.bind("<<ComboboxSelected>>", on_select)

command_list = tk.Listbox(root, width=100, height=20)
command_list.pack(pady=10)

root.mainloop()
