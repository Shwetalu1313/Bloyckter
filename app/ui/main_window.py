import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter import ttk
import time
from app.core.hashing.pbkdf2 import hash_password
from app.data.repository import load_data, save_data
from app.core.protector.folder import FolderProtector
from app.data.models import FolderLock
from app.ui.dialogs.lock_dialogs import LockSettingsDialog

class FolderLockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔏 Bloyckter - Folder Vault")
        self.root.geometry("750x450")
        self.root.configure(bg="#f5f5f5") # Subtle light grey background

        # Style Configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=30, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # Main Layout Containers
        self.main_container = tk.Frame(self.root, bg="#f5f5f5")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.left_panel = tk.Frame(self.main_container, bg="#f5f5f5")
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))

        self.right_panel = tk.Frame(self.main_container, bg="#f5f5f5")
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._setup_sidebar()
        self._setup_treeview()
        
        # Initial Data Load
        self.refresh_table()
        self.update_time_column()

    def _setup_sidebar(self):
        """Creates a clean sidebar for actions."""
        # Folder Actions Group
        action_frame = tk.LabelFrame(
            self.left_panel, text=" Actions ", font=("Segoe UI", 9, "bold"),
            bg="#f5f5f5", padx=10, pady=10
        )
        action_frame.pack(fill="x", pady=(0, 10))

        tk.Button(
            action_frame, text="➕ Add & Lock", command=self.add_and_lock_folder,
            bg="#2ecc71", fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", height=2, cursor="hand2"
        ).pack(fill="x", pady=5)

        tk.Button(
            action_frame, text="🔓 Unlock Folder", command=self.unlock_selected,
            bg="#3498db", fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", height=2, cursor="hand2"
        ).pack(fill="x", pady=5)

        # Settings Group
        settings_frame = tk.LabelFrame(
            self.left_panel, text=" Security ", font=("Segoe UI", 9, "bold"),
            bg="#f5f5f5", padx=10, pady=10
        )
        settings_frame.pack(fill="x")

        tk.Button(
            settings_frame, text="🔑 Change Password", command=self.open_change_password_dialog,
            bg="#95a5a6", fg="white", font=("Segoe UI", 9),
            relief="flat", cursor="hand2"
        ).pack(fill="x", pady=5)

    def _setup_treeview(self):
        """Initializes the data table with a scrollbar."""
        columns = ("no", "path", "status", "locked_at")
        
        # Container for Tree + Scrollbar
        tree_scroll_frame = tk.Frame(self.right_panel)
        tree_scroll_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_scroll_frame, columns=columns, show="headings")
        
        scrollbar = ttk.Scrollbar(tree_scroll_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.heading("no", text="#")
        self.tree.heading("path", text="Directory Path")
        self.tree.heading("status", text="Security Status")
        self.tree.heading("locked_at", text="Date Secured")

        self.tree.column("no", width=30, anchor="center")
        self.tree.column("path", width=300)
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("locked_at", width=100, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Row styling
        self.tree.tag_configure("waiting", background="#ffdada")  # Soft red for lockout
        self.tree.tag_configure("normal", background="white")

    def refresh_table(self):
        """Clears and repopulates the treeview."""
        self.tree.delete(*self.tree.get_children())
        data = load_data()

        for idx, (path, info) in enumerate(data.items(), start=1):
            locked_date = time.strftime("%Y-%m-%d", time.localtime(info["locked_at"]))
            self.tree.insert(
                "", "end", iid=path,
                values=(idx, path, "Secured", locked_date),
                tags=("normal",)
            )

    def update_time_column(self):
        """Periodic UI update for countdown timers."""
        data = load_data()
        now = time.time()

        for path, info in data.items():
            if not self.tree.exists(path): continue

            if now < info["locked_until"]:
                remaining = int(info["locked_until"] - now)
                status, tag = f"WAIT {remaining}s", "waiting"
            else:
                status, tag = "Secured", "normal"

            current_values = list(self.tree.item(path, "values"))
            current_values[2] = status
            self.tree.item(path, values=current_values, tags=(tag,))
        
        self.root.after(1000, self.update_time_column)

    def add_and_lock_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder to Secure")
        if not folder_path: return

        # Launch our new custom form
        dialog = LockSettingsDialog(self.root)
        self.root.wait_window(dialog) # Wait for user to finish

        if dialog.result:
            password, max_attempts, wait_time, cover_name = dialog.result
            
            # Hash using the salt-capable helper
            pwd_hash, pwd_salt = hash_password(password)

            folder = FolderLock(
                path=folder_path,
                password_hash=pwd_hash,
                password_salt=pwd_salt,
                max_attempts=max_attempts,
                wait_time=wait_time,
                cover_name=cover_name
            )

            success, msg = FolderProtector().lock(folder)
            if success:
                messagebox.showinfo("Success", "Folder secured with custom rules.")
                self.refresh_table()
            else:
                messagebox.showerror("Error", msg)

    def unlock_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Selection", "Please select a secured folder first.")
            return

        folder_path = self.tree.item(selected)["values"][1]
        password = simpledialog.askstring("Vault Access", "Enter password to unlock:", show="*")
        if not password: return

        success, msg = FolderProtector().unlock(folder_path, password)
        if success:
            messagebox.showinfo("Unlocked", "Folder is now accessible.")
            self.refresh_table()
        else:
            messagebox.showerror("Security Alert", msg)

    def open_change_password_dialog(self):
        selected = self.tree.focus()
        if not selected: return
        folder_path = self.tree.item(selected)["values"][1]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Password")
        dialog.geometry("300x200")
        dialog.grab_set()

        # Simple centered grid
        tk.Label(dialog, text="Current Password:").pack(pady=(10, 0))
        curr_e = tk.Entry(dialog, show="*", width=25); curr_e.pack()

        tk.Label(dialog, text="New Password:").pack(pady=(10, 0))
        new_e = tk.Entry(dialog, show="*", width=25); new_e.pack()

        def submit():
            success, msg = FolderProtector().change_password(folder_path, curr_e.get(), new_e.get())
            if success:
                messagebox.showinfo("Success", "Password updated.")
                dialog.destroy()
            else:
                messagebox.showerror("Error", msg)

        tk.Button(dialog, text="Update", command=submit, bg="#34495e", fg="white").pack(pady=20)
