import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from app.core.hashing.pbkdf2 import hash_password
from app.core.protector.folder import FolderProtector
from app.data.models import FolderLock
from app.data.repository import load_data
from app.data.settings_repository import load_settings, save_settings
from app.services.audit_service import AuditService
from app.services.mini_console_service import MiniConsoleService
from app.services.mount_service import test_path_connection
from app.services.workstation_lock_service import WorkstationLockService
from app.ui.dialogs.lock_dialogs import LockSettingsDialog
from app.ui.dialogs.mini_console_portal import MiniConsolePortal


class FolderLockerApp:
    COLORS = {
        "bg": "#F2F6FA",
        "card": "#FFFFFF",
        "card_border": "#D6E0EA",
        "text": "#1E2935",
        "muted": "#5D6D7E",
        "primary": "#0F766E",
        "primary_dark": "#0B5E58",
        "info": "#2563EB",
        "warning": "#D97706",
        "neutral": "#64748B",
        "success_soft": "#E7F8EF",
        "warning_soft": "#FFF4DD",
    }

    FONTS = {
        "title": ("Segoe UI Semibold", 17),
        "subtitle": ("Segoe UI", 10),
        "section": ("Segoe UI Semibold", 10),
        "body": ("Segoe UI", 10),
        "body_small": ("Segoe UI", 9),
        "button": ("Segoe UI Semibold", 9),
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Bloyckter")
        self.root.geometry("1200x730")
        self.root.minsize(1040, 640)
        self.root.configure(bg=self.COLORS["bg"])

        self.protector = FolderProtector()
        self.workstation_lock_service = WorkstationLockService(on_lock=self._on_auto_lock_triggered)
        self.console_service = MiniConsoleService(
            lock_callback=self._lock_from_console,
            connection_tester=test_path_connection,
        )
        self.console_portal = None

        self.auto_lock_var = tk.BooleanVar(value=False)
        self.idle_minutes_var = tk.StringVar(value="10")
        self.workstation_status_var = tk.StringVar(value="Auto-lock disabled")
        self.vault_count_var = tk.StringVar(value="0 secured items")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()

        self.main_container = tk.Frame(self.root, bg=self.COLORS["bg"])
        self.main_container.pack(fill="both", expand=True, padx=18, pady=18)

        self.left_panel = tk.Frame(self.main_container, bg=self.COLORS["bg"], width=350)
        self.left_panel.pack(side="left", fill="y", padx=(0, 18))
        self.left_panel.pack_propagate(False)

        self.right_panel = tk.Frame(self.main_container, bg=self.COLORS["bg"])
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._setup_sidebar()
        self._setup_right_panel()

        self.refresh_table()
        self.update_time_column()
        self._load_workstation_settings()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_styles(self):
        self.style.configure(
            "Modern.Treeview",
            rowheight=34,
            font=self.FONTS["body"],
            borderwidth=0,
            relief="flat",
            fieldbackground=self.COLORS["card"],
            background=self.COLORS["card"],
            foreground=self.COLORS["text"],
        )
        self.style.map(
            "Modern.Treeview",
            background=[("selected", "#DBF5EA")],
            foreground=[("selected", self.COLORS["text"])],
        )
        self.style.configure(
            "Modern.Treeview.Heading",
            font=("Segoe UI Semibold", 10),
            relief="flat",
            background="#EAF1F8",
            foreground=self.COLORS["text"],
            padding=(8, 8),
        )
        self.style.map("Modern.Treeview.Heading", background=[("active", "#EAF1F8")])
        self.style.configure("Vertical.TScrollbar", gripcount=0, troughcolor="#EAF1F8", borderwidth=0)

    def _create_card(self, parent, title: str, subtitle: str = ""):
        wrapper = tk.Frame(parent, bg=self.COLORS["bg"])
        wrapper.pack(fill="x", pady=(0, 12))

        card = tk.Frame(
            wrapper,
            bg=self.COLORS["card"],
            highlightbackground=self.COLORS["card_border"],
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=12,
        )
        card.pack(fill="x")

        tk.Label(
            card,
            text=title,
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
            font=self.FONTS["section"],
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                card,
                text=subtitle,
                bg=self.COLORS["card"],
                fg=self.COLORS["muted"],
                font=self.FONTS["body_small"],
            ).pack(anchor="w", pady=(2, 8))

        body = tk.Frame(card, bg=self.COLORS["card"])
        body.pack(fill="x")
        return body

    def _create_button(
        self,
        parent,
        text: str,
        command,
        bg: str,
        fg: str = "white",
        height: int = 1,
        pady: tuple[int, int] = (0, 8),
    ):
        tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            font=self.FONTS["button"],
            relief="flat",
            cursor="hand2",
            height=height,
            padx=8,
            pady=4,
            highlightthickness=0,
            bd=0,
        ).pack(fill="x", pady=pady)

    def _setup_sidebar(self):
        action_body = self._create_card(
            self.left_panel,
            "Vault Actions",
            "Secure and restore folders quickly.",
        )
        self._create_button(
            action_body,
            "Add and Lock Folder",
            self.add_and_lock_folder,
            bg=self.COLORS["primary"],
            height=2,
        )
        self._create_button(
            action_body,
            "Unlock Selected",
            self.unlock_selected,
            bg=self.COLORS["info"],
            height=2,
            pady=(0, 0),
        )

        security_body = self._create_card(
            self.left_panel,
            "Security",
            "Update vault credentials for selected item.",
        )
        self._create_button(
            security_body,
            "Change Password",
            self.open_change_password_dialog,
            bg=self.COLORS["neutral"],
            pady=(0, 0),
        )

        workstation_body = self._create_card(
            self.left_panel,
            "Workstation Protection",
            "Manual lock and idle-triggered session lock.",
        )
        self._create_button(
            workstation_body,
            "Lock Session Now",
            self.lock_workstation_now,
            bg=self.COLORS["warning"],
            height=2,
            pady=(0, 10),
        )

        tk.Checkbutton(
            workstation_body,
            text="Enable idle auto-lock",
            variable=self.auto_lock_var,
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
            activebackground=self.COLORS["card"],
            activeforeground=self.COLORS["text"],
            selectcolor=self.COLORS["card"],
            font=self.FONTS["body_small"],
        ).pack(anchor="w")

        idle_row = tk.Frame(workstation_body, bg=self.COLORS["card"])
        idle_row.pack(fill="x", pady=(8, 8))
        tk.Label(
            idle_row,
            text="Idle minutes",
            bg=self.COLORS["card"],
            fg=self.COLORS["muted"],
            font=self.FONTS["body_small"],
        ).pack(side="left")

        self.idle_spin = tk.Spinbox(
            idle_row,
            from_=1,
            to=240,
            textvariable=self.idle_minutes_var,
            width=7,
            font=self.FONTS["body_small"],
            relief="solid",
            bd=1,
            highlightthickness=0,
        )
        self.idle_spin.pack(side="right")

        self._create_button(
            workstation_body,
            "Apply Auto-lock Settings",
            command=lambda: self.apply_workstation_settings(show_message=True),
            bg=self.COLORS["primary_dark"],
            pady=(0, 6),
        )

        tk.Label(
            workstation_body,
            textvariable=self.workstation_status_var,
            bg=self.COLORS["card"],
            fg=self.COLORS["muted"],
            font=self.FONTS["body_small"],
            wraplength=280,
            justify="left",
        ).pack(anchor="w")

        console_body = self._create_card(
            self.left_panel,
            "Mini Console Portal",
            "Open popup console for remote path test and lock commands.",
        )
        self._create_button(
            console_body,
            "Open Console Portal",
            self.open_console_portal,
            bg=self.COLORS["primary_dark"],
            height=2,
            pady=(4, 0),
        )

    def _setup_right_panel(self):
        header_card = tk.Frame(
            self.right_panel,
            bg=self.COLORS["card"],
            highlightbackground=self.COLORS["card_border"],
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        header_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            header_card,
            text="Vault Dashboard",
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
            font=self.FONTS["title"],
        ).pack(anchor="w")
        tk.Label(
            header_card,
            text="Monitor secured paths, lockout status, and secured date.",
            bg=self.COLORS["card"],
            fg=self.COLORS["muted"],
            font=self.FONTS["subtitle"],
        ).pack(anchor="w", pady=(2, 6))
        tk.Label(
            header_card,
            textvariable=self.vault_count_var,
            bg=self.COLORS["card"],
            fg=self.COLORS["primary"],
            font=self.FONTS["section"],
        ).pack(anchor="w")

        table_card = tk.Frame(
            self.right_panel,
            bg=self.COLORS["card"],
            highlightbackground=self.COLORS["card_border"],
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        table_card.pack(fill="both", expand=True)

        columns = ("no", "path", "cover", "status", "locked_at")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", style="Modern.Treeview")
        scrollbar = ttk.Scrollbar(table_card, orient="vertical", style="Vertical.TScrollbar", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.heading("no", text="#")
        self.tree.heading("path", text="Directory Path")
        self.tree.heading("cover", text="Cover Name")
        self.tree.heading("status", text="Status")
        self.tree.heading("locked_at", text="Secured On")

        self.tree.column("no", width=46, anchor="center")
        self.tree.column("path", width=470, anchor="w")
        self.tree.column("cover", width=170, anchor="center")
        self.tree.column("status", width=160, anchor="center")
        self.tree.column("locked_at", width=130, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("waiting", background=self.COLORS["warning_soft"])
        self.tree.tag_configure("normal", background=self.COLORS["card"])

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
        count = len(data)
        self.vault_count_var.set(f"{count} secured item{'s' if count != 1 else ''}")

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
            messagebox.showerror("Invalid Value", "Idle minutes must be a number between 1 and 240.")
            return None

        if minutes < 1 or minutes > 240:
            messagebox.showerror("Invalid Value", "Idle minutes must be a number between 1 and 240.")
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
        dialog.geometry("420x280")
        dialog.resizable(False, False)
        dialog.configure(bg=self.COLORS["bg"])
        dialog.grab_set()

        card = tk.Frame(
            dialog,
            bg=self.COLORS["card"],
            highlightbackground=self.COLORS["card_border"],
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(
            card,
            text="Password Update",
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
            font=("Segoe UI Semibold", 13),
        ).pack(anchor="w")
        tk.Label(
            card,
            text="Enter current password and choose a new one.",
            bg=self.COLORS["card"],
            fg=self.COLORS["muted"],
            font=self.FONTS["body_small"],
        ).pack(anchor="w", pady=(2, 12))

        tk.Label(card, text="Current Password", bg=self.COLORS["card"], fg=self.COLORS["text"], font=self.FONTS["body_small"]).pack(anchor="w")
        curr_e = tk.Entry(card, show="*", width=36, font=self.FONTS["body"])
        curr_e.pack(fill="x", pady=(2, 10))

        tk.Label(card, text="New Password", bg=self.COLORS["card"], fg=self.COLORS["text"], font=self.FONTS["body_small"]).pack(anchor="w")
        new_e = tk.Entry(card, show="*", width=36, font=self.FONTS["body"])
        new_e.pack(fill="x", pady=(2, 14))

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

        actions = tk.Frame(card, bg=self.COLORS["card"])
        actions.pack(fill="x")
        tk.Button(
            actions,
            text="Cancel",
            command=dialog.destroy,
            bg="#E5EAF0",
            fg=self.COLORS["text"],
            activebackground="#D9E2EC",
            activeforeground=self.COLORS["text"],
            relief="flat",
            cursor="hand2",
            font=self.FONTS["button"],
            padx=10,
            pady=6,
            bd=0,
        ).pack(side="left")
        tk.Button(
            actions,
            text="Update Password",
            command=submit,
            bg=self.COLORS["primary"],
            fg="white",
            activebackground=self.COLORS["primary"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=self.FONTS["button"],
            padx=12,
            pady=6,
            bd=0,
        ).pack(side="right")

        curr_e.focus_set()
        dialog.bind("<Return>", lambda _evt: submit())

    def on_close(self):
        if self.console_portal and self.console_portal.winfo_exists():
            self.console_portal.destroy()
        self.workstation_lock_service.stop()
        self.root.destroy()

    def open_console_portal(self):
        if self.console_portal and self.console_portal.winfo_exists():
            self.console_portal.focus_force()
            return
        self.console_portal = MiniConsolePortal(self.root, self.console_service)

    def _lock_from_console(
        self,
        path: str,
        password: str,
        max_attempts: int,
        wait_time: int,
        cover_name: str,
        is_invisible: bool,
    ) -> tuple[bool, str]:
        pwd_hash, pwd_salt = hash_password(password)

        folder = FolderLock(
            path=path,
            password_hash=pwd_hash,
            password_salt=pwd_salt,
            max_attempts=max_attempts,
            wait_time=wait_time,
            cover_name=cover_name,
            is_invisible=is_invisible,
        )

        success, msg = self.protector.lock(folder)
        if success:
            AuditService.record("CONSOLE_LOCK_OK", f"path={path}")
            self.refresh_table()
        else:
            AuditService.record_error("CONSOLE_LOCK_FAILED", f"path={path} reason={msg}")
        return success, msg
