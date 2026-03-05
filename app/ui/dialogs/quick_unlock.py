import os
import tkinter as tk
from tkinter import messagebox

from app.data.repository import load_data
from app.services.audit_service import AuditService
from app.services.extraction_service import ExtractionService


class QuickUnlockDialog:
    COLORS = {
        "bg": "#F2F6FA",
        "card": "#FFFFFF",
        "border": "#D6E0EA",
        "text": "#1E2935",
        "muted": "#5D6D7E",
        "primary": "#0F766E",
    }

    def __init__(self, root, target_file_path):
        self.root = root
        self.target_file_path = target_file_path
        self.root.title("Bloyckter - Quick Unlock")
        self.root.geometry("430x250")
        self.root.resizable(False, False)
        self.root.configure(bg=self.COLORS["bg"])
        self.root.eval("tk::PlaceWindow . center")

        card = tk.Frame(
            self.root,
            bg=self.COLORS["card"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(
            card,
            text="Vault Access",
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
            font=("Segoe UI Semibold", 14),
        ).pack(anchor="w")

        tk.Label(
            card,
            text=f"Target: {os.path.basename(target_file_path)}",
            bg=self.COLORS["card"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 10))

        tk.Label(
            card,
            text="Enter your password to open a temporary decrypted view.",
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
            font=("Segoe UI", 10),
            wraplength=360,
            justify="left",
        ).pack(anchor="w")

        self.password_entry = tk.Entry(card, show="*", width=34, font=("Segoe UI", 10))
        self.password_entry.pack(fill="x", pady=(12, 14))
        self.password_entry.focus_set()
        self.password_entry.bind("<Return>", lambda _event: self.attempt_unlock())

        actions = tk.Frame(card, bg=self.COLORS["card"])
        actions.pack(fill="x")

        tk.Button(
            actions,
            text="Cancel",
            command=self.root.destroy,
            bg="#E6ECF2",
            fg=self.COLORS["text"],
            activebackground="#E6ECF2",
            activeforeground=self.COLORS["text"],
            font=("Segoe UI Semibold", 9),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            bd=0,
        ).pack(side="left")

        tk.Button(
            actions,
            text="Unlock",
            command=self.attempt_unlock,
            bg=self.COLORS["primary"],
            fg="white",
            activebackground=self.COLORS["primary"],
            activeforeground="white",
            font=("Segoe UI Semibold", 9),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            bd=0,
        ).pack(side="right")

    def attempt_unlock(self):
        password = self.password_entry.get()
        if not password:
            messagebox.showerror("Error", "Password cannot be empty.")
            return

        data = load_data()
        original_path = None
        target_info = None

        for path, info in data.items():
            if info.get("locked_path") == self.target_file_path:
                original_path = path
                target_info = info
                break

        if not original_path:
            AuditService.record_error("QUICK_UNLOCK_FAILED", f"locked_path={self.target_file_path} reason=metadata_missing")
            messagebox.showerror("Error", "Vault metadata not found.")
            self.root.destroy()
            return

        from app.core.hashing.pbkdf2 import hash_password
        from app.data.models import FolderLock

        lock_model = FolderLock(**target_info)

        if lock_model.is_locked_out():
            AuditService.record_error("QUICK_UNLOCK_DENIED", f"path={original_path} reason=locked_out")
            messagebox.showerror("Security", f"Locked out. Wait {lock_model.remaining_wait()}s.")
            return

        test_hash, _ = hash_password(password, lock_model.password_salt)

        if test_hash == lock_model.password_hash:
            success, msg = ExtractionService.decrypt_and_open(self.target_file_path)
            if success:
                AuditService.record("QUICK_UNLOCK_OK", f"path={original_path}")
                messagebox.showinfo("Success", "Vault opened in temporary view.")
                self.root.destroy()
            else:
                AuditService.record_error("QUICK_UNLOCK_FAILED", f"path={original_path} reason={msg}")
                messagebox.showerror("Error", msg)
        else:
            from app.core.security.security_service import SecurityService

            _, fail_msg = SecurityService.handle_failed_attempt(original_path, lock_model, data)
            AuditService.record_error("QUICK_UNLOCK_DENIED", f"path={original_path} reason=invalid_password")
            messagebox.showerror("Access Denied", fail_msg)
