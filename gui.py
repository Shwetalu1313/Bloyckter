import tkinter as tk
from tkinter import Listbox, filedialog, messagebox, simpledialog

from helper import load_data, hash_password
from logic import lock_folder, unlock_folder, get_managed_folders
from models import FolderLock

#  ------ GUI Actions ------
def refresh_list():
    Listbox.delete(0, tk.END)
    for folder in get_managed_folders():
        Listbox.insert(tk.END, folder)


# add and lock folder
def add_and_lock_folder():

    # select folder
    folder_path = filedialog.askdirectory("Select Folder to Lock")
    if not folder_path:
        return

    password = simpledialog.askstring("Password", "Enter a password to lock the folder:", show='x')
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
        refresh_list()
    else:
        messagebox.showerror("Error", msg)

    refresh_list()

# unlock selected folder
def unlock_selected_folder():
    
    selection = Listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "No folder selected.")
        return

    folder_path = Listbox.get(selection[0])

    password = simpledialog.askstring("Password", "Enter the password to unlock the folder:", show='x')
    if not password:
        messagebox.showerror("Error", "Password cannot be empty.")
        return

    success, msg = unlock_folder(folder_path, password)
    if success:
        messagebox.showinfo("Unlocked 🔓", msg)
        refresh_list()
    else:
        messagebox.showerror("Error", msg)

    refresh_list()


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
    , command=unlock_selected_folder
    ).pack(pady=5)

# Folder List
listbox = tk.Listbox(root, width=75, height=10)
listbox.pack(pady=10)

# initial refresh
refresh_list()

root.mainloop()