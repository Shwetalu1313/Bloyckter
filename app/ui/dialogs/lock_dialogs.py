import tkinter as tk
from tkinter import messagebox


class LockSettingsDialog(tk.Toplevel):
    """
    Modal dialog for lock parameters:
    password, cover name, max attempts, wait time, and visibility mode.
    """

    COLORS = {
        "bg": "#F2F6FA",
        "card": "#FFFFFF",
        "border": "#D6E0EA",
        "text": "#1E2935",
        "muted": "#5D6D7E",
        "primary": "#0F766E",
        "neutral": "#E6ECF2",
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Security Settings")
        self.geometry("470x470")
        self.resizable(False, False)
        self.configure(bg=self.COLORS["bg"])
        self.result = None
        self.grab_set()

        card = tk.Frame(
            self,
            bg=self.COLORS["card"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(
            card,
            text="Secure Folder",
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
            font=("Segoe UI Semibold", 14),
        ).pack(anchor="w")

        tk.Label(
            card,
            text="Set lock policy and disguise details before securing the folder.",
            bg=self.COLORS["card"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 14))

        tk.Label(card, text="Vault Password", bg=self.COLORS["card"], fg=self.COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w")
        self.pwd_entry = tk.Entry(card, show="*", width=38, font=("Segoe UI", 10))
        self.pwd_entry.pack(fill="x", pady=(2, 10))

        tk.Label(card, text="Cover Name (Alias)", bg=self.COLORS["card"], fg=self.COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w")
        self.cover_entry = tk.Entry(card, width=38, font=("Segoe UI", 10))
        self.cover_entry.insert(0, "System_Data_Cache")
        self.cover_entry.pack(fill="x", pady=(2, 10))

        row = tk.Frame(card, bg=self.COLORS["card"])
        row.pack(fill="x", pady=(0, 10))

        left = tk.Frame(row, bg=self.COLORS["card"])
        left.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(left, text="Max Failed Attempts", bg=self.COLORS["card"], fg=self.COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w")
        self.attempts_entry = tk.Spinbox(left, from_=1, to=10, width=10, font=("Segoe UI", 10))
        self.attempts_entry.delete(0, "end")
        self.attempts_entry.insert(0, "3")
        self.attempts_entry.pack(fill="x", pady=(2, 0))

        right = tk.Frame(row, bg=self.COLORS["card"])
        right.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(right, text="Lockout Duration (sec)", bg=self.COLORS["card"], fg=self.COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w")
        self.wait_entry = tk.Spinbox(right, from_=15, to=86400, width=10, font=("Segoe UI", 10))
        self.wait_entry.delete(0, "end")
        self.wait_entry.insert(0, "180")
        self.wait_entry.pack(fill="x", pady=(2, 0))

        self.invisible_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            card,
            text="Hide from File Explorer after lock",
            variable=self.invisible_var,
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
            activebackground=self.COLORS["card"],
            activeforeground=self.COLORS["text"],
            selectcolor=self.COLORS["card"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(6, 16))

        actions = tk.Frame(card, bg=self.COLORS["card"])
        actions.pack(fill="x")

        tk.Button(
            actions,
            text="Cancel",
            command=self.destroy,
            bg=self.COLORS["neutral"],
            fg=self.COLORS["text"],
            activebackground=self.COLORS["neutral"],
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
            text="Confirm and Secure",
            bg=self.COLORS["primary"],
            fg="white",
            activebackground=self.COLORS["primary"],
            activeforeground="white",
            font=("Segoe UI Semibold", 9),
            command=self.on_confirm,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            bd=0,
        ).pack(side="right")

        self.pwd_entry.focus_set()
        self.bind("<Return>", lambda _evt: self.on_confirm())
        self.bind("<Escape>", lambda _evt: self.destroy())

    def on_confirm(self):
        pwd = self.pwd_entry.get()
        cover = self.cover_entry.get().strip()

        try:
            attempts = int(self.attempts_entry.get())
            wait = int(self.wait_entry.get())

            if not pwd:
                raise ValueError("Password is required.")
            if len(pwd) < 8:
                raise ValueError("Password must be at least 8 characters.")
            if not cover:
                raise ValueError("A cover name is required for obfuscation.")
            if attempts < 1 or attempts > 10:
                raise ValueError("Max attempts must be between 1 and 10.")
            if wait < 15 or wait > 86400:
                raise ValueError("Lockout duration must be between 15 and 86400 seconds.")

            self.result = (pwd, attempts, wait, cover, self.invisible_var.get())
            self.destroy()

        except ValueError as ex:
            messagebox.showerror("Invalid Input", str(ex))
