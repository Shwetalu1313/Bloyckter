import tkinter as tk
from tkinter import messagebox
from app.data.repository import load_data
from app.core.protector.folder import FolderProtector
from app.services.extraction_service import ExtractionService

class QuickUnlockDialog:
    def __init__(self, root, target_file_path):
        self.root = root
        self.target_file_path = target_file_path
        self.root.title("Quick Unlock -_-")
        self.root.geometry("300x150")
        self.root.eval('tk::PlaceWindow . center')
        self.root.resizable(False, False)

        # UI Elements
        tk.Label(self.root, text="This value is locked", font=("Segoe UI", 10, "bold")).pack(pady=10)
        tk.Label(self.root, text="Enter your password to unlock:").pack()

        self.password_entry = tk.Entry(self.root, show="*", width=30)
        self.password_entry.pack(pady=5)
        self.password_entry.focus_set()

        # Bind Enter key to unlock action
        self.password_entry.bind("<Return>", lambda event: self.attempt_unlock())

        tk.Button(self.root, text="Unlock", command=self.attempt_unlock).pack(pady=10)

    def attempt_unlock(self):
        password = self.password_entry.get()
        if not password:
            messagebox.showerror("Error", "Password cannot be empty.")
            return
        
        data = load_data()
        original_path = None
        target_info = None

        # Find the metadata matching this file
        for path, info in data.items():
            if info.get("locked_path") == self.target_file_path:
                original_path = path
                target_info = info
                break

        if not original_path:
            messagebox.showerror("Error", "Vault metadata not found.")
            self.root.destroy()
            return

        # NEW: Verify the password
        from app.core.hashing.pbkdf2 import hash_password
        from app.data.models import FolderLock

        # Reconstruct the model to check lockout status
        lock_model = FolderLock(**target_info)
        
        if lock_model.is_locked_out():
            messagebox.showerror("Security", f"Locked out! Wait {lock_model.remaining_wait()}s.")
            return

        # Hash the input and compare
        test_hash, _ = hash_password(password, lock_model.password_salt)
        
        if test_hash == lock_model.password_hash:
            # ONLY call extraction if password is correct
            success, msg = ExtractionService.decrypt_and_open(self.target_file_path)
            if success:
                messagebox.showinfo("Success", "Vault opened in temporary view!")
                self.root.destroy()
            else:
                messagebox.showerror("Error", msg)
        else:
            # Handle failed attempt (this will update attempts/lockout)
            from app.core.security.security_service import SecurityService
            _, fail_msg = SecurityService.handle_failed_attempt(original_path, lock_model, data)
            messagebox.showerror("Access Denied", fail_msg)
