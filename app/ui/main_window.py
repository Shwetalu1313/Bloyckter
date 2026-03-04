import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from app.core.hashing.pbkdf2 import hash_password
from app.core.protector.folder import FolderProtector
from app.data.models import FolderLock
from app.data.repository import load_data
from app.data.settings_repository import load_settings, save_settings
from app.services.audit_service import AuditService
from app.services.workstation_lock_service import WorkstationLockService
from app.ui.dialogs.lock_dialogs import LockSettingsDialog


class FolderLockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bloyckter - Folder Vault")
        self.root.geometry("820x500")
        self.root.configure(bg="#f5f5f5")

        self.protector = FolderProtector()
        self.workstation_lock_service = WorkstationLockService(on_lock=self._on_auto_lock_triggered)

        self.auto_lock_var = tk.BooleanVar(value=False)
        self.idle_minutes_var = tk.StringVar(value="10")
        self.workstation_status_var = tk.StringVar(value="Auto-lock disabled")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=30, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.main_container = tk.Frame(self.root, bg="#f5f5f5")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.left_panel = tk.Frame(self.main_container, bg="#f5f5f5")
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))

        self.right_panel = tk.Frame(self.main_container, bg="#f5f5f5")
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._setup_sidebar()
        self._setup_treeview()

        self.refresh_table()
        self.update_time_column()
        self._load_workstation_settings()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_sidebar(self):
        action_frame = tk.LabelFrame(
            self.left_panel,
            text=" Actions ",
            font=("Segoe UI", 9, "bold"),
            bg="#f5f5f5",
            padx=10,
            pady=10,
        )
        action_frame.pack(fill="x", pady=(0, 10))

        tk.Button(
            action_frame,
            text="Add & Lock",
            command=self.add_and_lock_folder,
            bg="#2ecc71",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            height=2,
            cursor="hand2",
        ).pack(fill="x", pady=5)

        tk.Button(
            action_frame,
            text="Unlock Folder",
            command=self.unlock_selected,
            bg="#3498db",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            height=2,
            cursor="hand2",
        ).pack(fill="x", pady=5)

        settings_frame = tk.LabelFrame(
            self.left_panel,
            text=" Security ",
            font=("Segoe UI", 9, "bold"),
            bg="#f5f5f5",
            padx=10,
            pady=10,
        )
        settings_frame.pack(fill="x")

        tk.Button(
            settings_frame,
            text="Change Password",
            command=self.open_change_password_dialog,
            bg="#95a5a6",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
        ).pack(fill="x", pady=5)

        workstation_frame = tk.LabelFrame(
            self.left_panel,
            text=" Workstation Security ",
            font=("Segoe UI", 9, "bold"),
            bg="#f5f5f5",
            padx=10,
            pady=10,
        )
        workstation_frame.pack(fill="x", pady=(10, 0))

        tk.Button(
            workstation_frame,
            text="Lock Session Now",
            command=self.lock_workstation_now,
            bg="#e67e22",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            height=2,
        ).pack(fill="x", pady=(0, 8))

        tk.Checkbutton(
            workstation_frame,
            text="Enable idle auto-lock",
            variable=self.auto_lock_var,
            bg="#f5f5f5",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        idle_row = tk.Frame(workstation_frame, bg="#f5f5f5")
        idle_row.pack(fill="x", pady=(6, 6))

        tk.Label(idle_row, text="Idle minutes:", bg="#f5f5f5", font=("Segoe UI", 9)).pack(side="left")
        self.idle_spin = tk.Spinbox(idle_row, from_=1, to=240, textvariable=self.idle_minutes_var, width=6)
        self.idle_spin.pack(side="right")

        tk.Button(
            workstation_frame,
            text="Apply Auto-lock Settings",
            command=lambda: self.apply_workstation_settings(show_message=True),
            bg="#34495e",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
        ).pack(fill="x", pady=(2, 6))

        tk.Label(
            workstation_frame,
            textvariable=self.workstation_status_var,
            bg="#f5f5f5",
            fg="#2c3e50",
            font=("Segoe UI", 8, "italic"),
            wraplength=180,
            justify="left",
        ).pack(anchor="w")

    def _setup_treeview(self):
        columns = ("no", "path", "cover", "status", "locked_at")

        tree_scroll_frame = tk.Frame(self.right_panel)
        tree_scroll_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_scroll_frame, columns=columns, show="headings")
        scrollbar = ttk.Scrollbar(tree_scroll_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.heading("no", text="#")
        self.tree.heading("path", text="Directory Path")
        self.tree.heading("cover", text="Cover Name")
        self.tree.heading("status", text="Security Status")
        self.tree.heading("locked_at", text="Date Secured")

        self.tree.column("no", width=40, anchor="center")
        self.tree.column("path", width=380)
        self.tree.column("cover", width=150, anchor="center")
        self.tree.column("status", width=140, anchor="center")
        self.tree.column("locked_at", width=120, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("waiting", background="#ffdada")
        self.tree.tag_configure("normal", background="white")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        data = load_data()

        for idx, (path, info) in enumerate(data.items(), start=1):
            locked_date = time.strftime("%Y-%m-%d", time.localtime(info.get("locked_at", time.time())))
            cover_name = info.get("cover_name") or info.get("cover") or ""
            self.tree.insert(
                "",
                "end",
                iid=path,
                values=(idx, path, cover_name, "Secured", locked_date),
                tags=("normal",),
            )

    def update_time_column(self):
        data = load_data()
        now = time.time()

        for path, info in data.items():
            if not self.tree.exists(path):
                continue

            locked_until = info.get("locked_until", 0)
            if now < locked_until:
                remaining = int(locked_until - now)
                status, tag = f"WAIT {remaining}s", "waiting"
            else:
                status, tag = "Secured", "normal"

            current_values = list(self.tree.item(path, "values"))
            current_values[3] = status
            self.tree.item(path, values=current_values, tags=(tag,))

        self.root.after(1000, self.update_time_column)

    def _load_workstation_settings(self):
        settings = load_settings()
        self.auto_lock_var.set(settings["workstation_auto_lock_enabled"])
        self.idle_minutes_var.set(str(settings["workstation_idle_minutes"]))
        self.apply_workstation_settings(show_message=False)

    def _parse_idle_minutes(self):
        try:
            minutes = int(self.idle_minutes_var.get())
        except ValueError:
            messagebox.showerror("Invalid value", "Idle minutes must be a number between 1 and 240.")
            return None

        if minutes < 1 or minutes > 240:
            messagebox.showerror("Invalid value", "Idle minutes must be a number between 1 and 240.")
            return None
        return minutes

    def apply_workstation_settings(self, show_message: bool = False):
        minutes = self._parse_idle_minutes()
        if minutes is None:
            return

        enabled = self.auto_lock_var.get()
        save_settings(
            {
                "workstation_auto_lock_enabled": enabled,
                "workstation_idle_minutes": minutes,
            }
        )

        if enabled:
            self.workstation_lock_service.start(minutes * 60)
            self.workstation_status_var.set(f"Auto-lock enabled ({minutes} min idle).")
        else:
            self.workstation_lock_service.stop()
            self.workstation_status_var.set("Auto-lock disabled.")

        if show_message:
            messagebox.showinfo("Settings Saved", "Workstation lock settings have been updated.")

    def _on_auto_lock_triggered(self):
        self.root.after(0, lambda: self.workstation_status_var.set("Session locked by auto-lock policy."))
        AuditService.record("WORKSTATION_LOCKED", "trigger=auto_idle")

    def lock_workstation_now(self):
        success = self.workstation_lock_service.lock_now()
        if success:
            AuditService.record("WORKSTATION_LOCKED", "trigger=manual")
            messagebox.showinfo("Locked", "Windows session lock command sent.")
        else:
            AuditService.record_error("WORKSTATION_LOCK_FAILED", "trigger=manual")
            messagebox.showerror("Error", "Unable to lock the current workstation session.")

    def add_and_lock_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder to Secure")
        if not folder_path:
            return

        dialog = LockSettingsDialog(self.root)
        self.root.wait_window(dialog)

        if dialog.result:
            password, max_attempts, wait_time, cover_name, is_invisible = dialog.result
            pwd_hash, pwd_salt = hash_password(password)

            folder = FolderLock(
                path=folder_path,
                password_hash=pwd_hash,
                password_salt=pwd_salt,
                max_attempts=max_attempts,
                wait_time=wait_time,
                cover_name=cover_name,
                is_invisible=is_invisible,
            )

            success, msg = self.protector.lock(folder)
            if success:
                messagebox.showinfo("Success", "Folder secured with custom rules.")
                self.refresh_table()
            else:
                AuditService.record_error("FOLDER_LOCK_FAILED", f"path={folder_path} reason={msg}")
                messagebox.showerror("Error", msg)

    def unlock_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Selection", "Please select a secured folder first.")
            return

        folder_path = self.tree.item(selected)["values"][1]
        password = simpledialog.askstring("Vault Access", "Enter password to unlock:", show="*")
        if not password:
            return

        success, msg = self.protector.unlock(folder_path, password)
        if success:
            messagebox.showinfo("Unlocked", "Folder is now accessible.")
            self.refresh_table()
        else:
            AuditService.record_error("FOLDER_UNLOCK_FAILED", f"path={folder_path} reason={msg}")
            messagebox.showerror("Security Alert", msg)

    def open_change_password_dialog(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Selection", "Please select a secured folder first.")
            return

        folder_path = self.tree.item(selected)["values"][1]

        dialog = tk.Toplevel(self.root)
        dialog.title("Update Password")
        dialog.geometry("320x220")
        dialog.grab_set()

        tk.Label(dialog, text="Current Password:").pack(pady=(10, 0))
        curr_e = tk.Entry(dialog, show="*", width=25)
        curr_e.pack()

        tk.Label(dialog, text="New Password:").pack(pady=(10, 0))
        new_e = tk.Entry(dialog, show="*", width=25)
        new_e.pack()

        def submit():
            current_password = curr_e.get().strip()
            new_password = new_e.get().strip()
            if not current_password or not new_password:
                messagebox.showerror("Error", "Both password fields are required.")
                return

            success, msg = self.protector.change_password(folder_path, current_password, new_password)
            if success:
                messagebox.showinfo("Success", "Password updated.")
                dialog.destroy()
            else:
                AuditService.record_error("PASSWORD_CHANGE_FAILED", f"path={folder_path} reason={msg}")
                messagebox.showerror("Error", msg)

        tk.Button(dialog, text="Update", command=submit, bg="#34495e", fg="white").pack(pady=20)

    def on_close(self):
        self.workstation_lock_service.stop()
        self.root.destroy()
