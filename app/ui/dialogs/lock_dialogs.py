import tkinter as tk
from tkinter import messagebox

class LockSettingsDialog(tk.Toplevel):
    """
    Custom popup to collect all locking parameters at once, 
    including the new Cover Name for obfuscation.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Security Settings")
        self.geometry("340x320")
        self.resizable(False, False)
        self.result = None
        self.grab_set()  # Make dialog modal

        # Main layout frame
        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        # 1. Password Field
        tk.Label(frame, text="Set Vault Password:").pack(anchor="w")
        self.pwd_entry = tk.Entry(frame, show="*", width=35)
        self.pwd_entry.pack(pady=(0, 10))

        # 2. NEW: Cover Name (Obfuscation Alias)
        tk.Label(frame, text="Cover Name (File Explorer Alias):").pack(anchor="w")
        self.cover_entry = tk.Entry(frame, width=35)
        self.cover_entry.insert(0, "System_Data_Cache") # Default fake name
        self.cover_entry.pack(pady=(0, 10))

        # 3. Max Attempts
        tk.Label(frame, text="Max Failed Attempts:").pack(anchor="w")
        self.attempts_entry = tk.Entry(frame, width=35)
        self.attempts_entry.insert(0, "3")
        self.attempts_entry.pack(pady=(0, 10))

        # 4. Wait Time
        tk.Label(frame, text="Lockout Duration (seconds):").pack(anchor="w")
        self.wait_entry = tk.Entry(frame, width=35)
        self.wait_entry.insert(0, "180")
        self.wait_entry.pack(pady=(0, 20))

        # Confirm Button
        btn_lock = tk.Button(
            frame, text="Confirm & Secure", bg="#2ecc71", fg="white",
            font=("Segoe UI", 9, "bold"), command=self.on_confirm,
            relief="flat", cursor="hand2", height=2
        )
        btn_lock.pack(fill="x")

    def on_confirm(self):
        pwd = self.pwd_entry.get()
        cover = self.cover_entry.get().strip()
        
        try:
            attempts = int(self.attempts_entry.get())
            wait = int(self.wait_entry.get())
            
            if not pwd: 
                raise ValueError("Password is required.")
            if not cover: 
                raise ValueError("A cover name is required for obfuscation.")
            
            # Return all parameters to the main window
            self.result = (pwd, attempts, wait, cover)
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))