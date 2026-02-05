import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

class LockSettingsDialog(tk.Toplevel):
    """Custom popup to collect all locking parameters at once."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Security Settings")
        self.geometry("320x280")
        self.resizable(False, False)
        self.result = None
        self.grab_set()  # Make dialog modal

        # Layout
        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Set Vault Password:").pack(anchor="w")
        self.pwd_entry = tk.Entry(frame, show="*", width=30)
        self.pwd_entry.pack(pady=(0, 10))

        tk.Label(frame, text="Max Failed Attempts:").pack(anchor="w")
        self.attempts_entry = tk.Entry(frame, width=30)
        self.attempts_entry.insert(0, "3")
        self.attempts_entry.pack(pady=(0, 10))

        tk.Label(frame, text="Lockout Duration (seconds):").pack(anchor="w")
        self.wait_entry = tk.Entry(frame, width=30)
        self.wait_entry.insert(0, "180")
        self.wait_entry.pack(pady=(0, 20))

        btn_lock = tk.Button(
            frame, text="Confirm & Lock", bg="#2ecc71", fg="white",
            font=("Segoe UI", 9, "bold"), command=self.on_confirm
        )
        btn_lock.pack(fill="x")

    def on_confirm(self):
        pwd = self.pwd_entry.get()
        try:
            attempts = int(self.attempts_entry.get())
            wait = int(self.wait_entry.get())
            if not pwd: raise ValueError("Password required")
            
            self.result = (pwd, attempts, wait)
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e) if "Password" in str(e) else "Attempts and Wait Time must be numbers.")