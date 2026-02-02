import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import time
from helper import load_data, hash_password
from logic import lock_folder, unlock_folder, get_managed_folders
from models import FolderLock

#  ------ GUI Actions ------
# def refresh_list():
#     listbox.delete(0, tk.END)
#     for folder in get_managed_folders():
#         listbox.insert(tk.END, folder)

# ------ Refresh Table ------
def refresh_table():
    tree.delete(*tree.get_children())
    data = load_data()

    for idx, (path, info) in enumerate(data.items(), start=1):
        # Status calculation
        locked_date = time.strftime(
            "%Y-%m-%d",
            time.localtime(info["locked_at"])
        )

        tree.insert(
            "",
            "end",
            iid=path,
            values=(idx, path, "locked", locked_date),
            tags=("normal",)
        )


# add and lock folder
def add_and_lock_folder():

    # select folder
    folder_path = filedialog.askdirectory(title="Select Folder to Lock")
    if not folder_path:
        return

    password = simpledialog.askstring("Password", "Enter a password to lock the folder:", show='*')
    if not password:
        messagebox.showerror("Error", "Password cannot be empty.")
        return
    
    # Max Attempts
    max_attempts = simpledialog.askinteger(
        "Attempts", "Enter maximum number of allowed attempts:",
        minvalue=1, 
        initialvalue=3
    )

    if max_attempts is None:
        return
    
    # waiting time
    wait_time = simpledialog.askinteger(
        "Wait Time", "Enter wait time (in seconds) after max attempts reached:",
        minvalue=10,
        initialvalue=180
    )

    # folder obj
    folder = FolderLock(
        path=folder_path,
        password_hash=hash_password(password),
        max_attempts=max_attempts,
        wait_time=wait_time
    )

    success, msg = lock_folder(folder)
    if success:
        messagebox.showinfo("Success", msg)
    else:
        messagebox.showerror("Error", msg)

    refresh_table()


# Unlock selected Row
def unlock_selected():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Select", "Select a folder first.")
        return

    folder_path = tree.item(selected)["values"][1]

    password = simpledialog.askstring(
        "Unlock", "Enter password:", show="*"
    )
    if not password:
        return

    success, msg = unlock_folder(folder_path, password)
    if success:
        messagebox.showinfo("Unlocked 🔓", msg)
    else:
        messagebox.showerror("Error", msg)
    refresh_table()

# update time column
def update_time_column():
    data = load_data()
    now = time.time()

    for path, info in data.items():
        if not tree.exists(path):
            continue

        if now < info["locked_until"]:
            remaining =  int(info["locked_until"] - now)
            status = f"WAIT {remaining}"
            tag = "waiting"

        else:
            status = "locked"
            tag = "normal"

        # update only the status column
        current_values = list(tree.item(path, "values"))
        current_values[2] = status
        tree.item(path, values=current_values, tags=(tag,))
    root.after(1000, update_time_column)




# unlock selected folder
# def unlock_selected_folder():
    
#     selection = listbox.curselection()
#     if not selection:
#         messagebox.showerror("Error", "No folder selected.")
#         return

#     folder_path = listbox.get(selection[0])

#     password = simpledialog.askstring("Password", "Enter the password to unlock the folder:", show='x')
#     if not password:
#         messagebox.showerror("Error", "Password cannot be empty.")
#         return

#     success, msg = unlock_folder(folder_path, password)
#     if success:
#         messagebox.showinfo("Unlocked 🔓", msg)
#         refresh_list()
#     else:
#         messagebox.showerror("Error", msg)

#     refresh_list()


# -------- Main Window --------
root = tk.Tk()
root.title("🔏 Folder Locker")
root.geometry("520x320")
root.resizable(False, False)

# Buttons
tk.Button(
    root, 
    text="➕ Add & Lock Folder", 
    command=add_and_lock_folder
    ).pack(pady=5)

tk.Button(
    root,   
    text = "🔓 Unlock Selected Folder"
    , command=unlock_selected
    ).pack(pady=5)

# Folder List
# listbox = tk.Listbox(root, width=75, height=10)
# listbox.pack(pady=10)

# Treeview / Listbox
columns = ("no", "path", "status", "locked_at")

tree = ttk.Treeview(root, columns=columns, show="headings", height=10)

tree.heading("no", text="No")
tree.heading("path", text="Folder Path")
tree.heading("status", text="Status / Wait Time")
tree.heading("locked_at", text="Locked Date")

tree.column("no", width=40, anchor="center")
tree.column("path", width=260)
tree.column("status", width=120, anchor="center")
tree.column("locked_at", width=100, anchor="center")

tree.pack(pady=10)

# Raw colour
tree.tag_configure("waiting", background="#f86f6f")  # light red
tree.tag_configure("normal", background="#ffffff")  # white

# initial refresh
refresh_table()
update_time_column()