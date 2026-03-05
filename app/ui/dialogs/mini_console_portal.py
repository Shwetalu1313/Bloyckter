import tkinter as tk
from tkinter import messagebox


class MiniConsolePortal(tk.Toplevel):
    """
    Popup console window for remote path testing and remote lock commands.
    """

    COLORS = {
        "bg": "#E8EFF7",
        "glass": "#F7FBFF",
        "glass_deep": "#EAF2FA",
        "border": "#C7D6E6",
        "text": "#132437",
        "muted": "#4A6076",
        "primary": "#0F766E",
        "secondary": "#2E4F73",
        "danger": "#9F2A2A",
        "console_bg": "#0A1628",
        "console_text": "#C4F9E3",
    }

    def __init__(self, parent, console_service):
        super().__init__(parent)
        self.console_service = console_service

        self.title("Mini Console Portal")
        self.geometry("880x560")
        self.minsize(680, 420)
        self.configure(bg=self.COLORS["bg"])

        try:
            # Soft glass-like effect on supported platforms.
            self.attributes("-alpha", 0.97)
        except tk.TclError:
            pass

        self._build_ui()
        self._append_line("Portal ready. Type 'help' for commands.")

        self.bind("<Return>", lambda _evt: self.run_command())
        self.bind("<Escape>", lambda _evt: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.entry.focus_set()

    def _build_ui(self):
        container = tk.Frame(self, bg=self.COLORS["bg"], padx=16, pady=16)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        header = tk.Frame(
            container,
            bg=self.COLORS["glass"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        tk.Label(
            header,
            text="Remote Lock Console",
            bg=self.COLORS["glass"],
            fg=self.COLORS["text"],
            font=("Segoe UI Semibold", 16),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Run: help, test <path>, lock <path> --password <pwd> ...",
            bg=self.COLORS["glass"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(
            container,
            bg=self.COLORS["glass_deep"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self.output = tk.Text(
            body,
            bg=self.COLORS["console_bg"],
            fg=self.COLORS["console_text"],
            insertbackground=self.COLORS["console_text"],
            font=("Cascadia Mono", 10),
            relief="flat",
            wrap="word",
            padx=10,
            pady=10,
            bd=0,
        )
        self.output.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        self.output.configure(state="disabled")

        self.entry = tk.Entry(
            body,
            font=("Cascadia Mono", 10),
            bg="#FFFFFF",
            fg=self.COLORS["text"],
            relief="solid",
            bd=1,
            highlightthickness=0,
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        actions = tk.Frame(body, bg=self.COLORS["glass_deep"])
        actions.grid(row=1, column=1, sticky="e")

        tk.Button(
            actions,
            text="Run",
            command=self.run_command,
            bg=self.COLORS["primary"],
            fg="white",
            activebackground=self.COLORS["primary"],
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            actions,
            text="Help",
            command=self.show_help,
            bg=self.COLORS["secondary"],
            fg="white",
            activebackground=self.COLORS["secondary"],
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            actions,
            text="Clear",
            command=self.clear_output,
            bg=self.COLORS["danger"],
            fg="white",
            activebackground=self.COLORS["danger"],
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=6,
        ).pack(side="left")

    def _append_line(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", f"{text}\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self._append_line("Console cleared.")

    def show_help(self):
        _ok, message = self.console_service.execute("help")
        self._append_line(message)

    def run_command(self):
        command = self.entry.get().strip()
        if not command:
            return

        self.entry.delete(0, "end")
        self._append_line(f"> {command}")
        success, message = self.console_service.execute(command)
        self._append_line(message)

        if command.lower().startswith("lock "):
            if success:
                messagebox.showinfo("Console Lock", message, parent=self)
            else:
                messagebox.showerror("Console Lock", message, parent=self)
