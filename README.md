# 🔐 Python Folder Locker (GUI)

A **Windows desktop application** built with **Python (Tkinter)** to lock folders using **per-folder passwords**, **attempt limits**, and **timed lockouts**, featuring **secure encrypted storage**.

This project focuses on **practical desktop security**, clean architecture, and real-world usability.

---

## ✨ Features

- 🔒 Lock multiple folders
- 🔑 Unique password **per folder**
- 🧂 Password hashing with **PBKDF2 + per-folder salt**
- 🔁 Configurable maximum failed attempts
- ⏳ Automatic lockout (cooldown) after failed attempts
- 🔐 Encrypted local storage (AES / Fernet)
- 🪟 Encryption key protected by **Windows DPAPI**
- 📁 Secure storage in **Windows AppData**
- 🖥️ Modern Tkinter GUI
- 🎨 Visual lockout countdown with color indication
- 🔑 Change password **without unlocking the folder**

---

## 🧠 How It Works (High-Level)

The application follows a tiered architecture to ensure data integrity and security:

1.  **GUI (Tkinter):** User interaction and folder selection.
2.  **Business Logic:** Manages attempts, timers, and state.
3.  **Encrypted Storage:** AES/Fernet layer for folder metadata.
4.  **Windows DPAPI:** User and machine-bound key protection.

- Folder metadata is encrypted at rest
- Encryption key is **never stored in plaintext**
- Each folder has its **own password salt**
- Data is isolated per Windows user

---

## 🔐 Security Design

### ✔ What Bloyckter Protects Against
- Casual access by other local users
- Curious coworkers
- Accidental folder access
- Copying encrypted files to another machine
- Simple brute-force attacks (rate-limited + PBKDF2)

### ❌ What Bloyckter Does NOT Protect Against
- Windows Administrators
- Disk removal / offline forensic attacks
- Malware running with user privileges

> [!WARNING]  
> This app is designed for **personal privacy and workflow protection**, not administrator-level or military-grade security.

## 🔑 Password Security

- Passwords are **never stored in plaintext**
- Each folder uses:
  - **PBKDF2-HMAC-SHA256**
  - **100,000 iterations**
  - **Unique random salt**
- Changing a password generates a **new salt** automatically

---

## 📁 Where Data Is Stored

All sensitive data is stored **outside the application folder** to prevent accidental deletion during updates:

`C:\Users\<USERNAME>\AppData\Local\Bloyckter`
* `data.enc` — Encrypted folder metadata.
* `key.blob` — DPAPI-protected encryption key.

> [!CAUTION]  
> Deleting these files will result in **data loss**, not data exposure. Locked folders will remain inaccessible without these metadata files.

---

## 🛠 Requirements

* **Windows OS**
* **Python 3.10+**
* **Python packages:**
    * `cryptography`
    * `pywin32`

### Installation

```bash
pip install -r requirements.txt
```

## ▶️ Run the Application

```bash
python gui.py
```
**Note:** Ensure your virtual environment is activated and you are running the command from the project root directory.

## 📦 Build Executable (Optional)
To create a standalone Windows executable:

```bash
pyinstaller --onefile --noconsole gui.py
```

The output `.exe` file will be generated in the `dist/` folder.

## ⚠️ Important Notes & Limitations

* **Manual Changes:** If a locked folder is renamed or moved manually, the app will no longer recognize it.
* **Data Recovery:** If AppData security files are deleted, locked folders cannot be recovered.
* **Direct Access:** Unlocking folders without opening the app is not supported by design to maintain security rules.

## 🚧 Planned Improvements

- [ ]📜 Audit log for failed unlock attempts
- [ ]🖱️ Right-click context menu (Explorer integration)
- [ ]🔔 System tray support
- [ ]🌙 Dark mode UI
- [ ]🔐 Password strength indicator
- [ ]📦 Installer package

