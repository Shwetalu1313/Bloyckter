# 🔐 Python Folder Locker (GUI)

A **Windows desktop application** built with **Python (Tkinter)** to lock folders using **per-folder passwords**, **attempt limits**, and **timed lockouts**, featuring **secure encrypted storage**.

This project focuses on **practical desktop security**, clean architecture, and real-world usability.

---

## ✨ Features

* 🔒 **Multi-Folder Locking:** Secure multiple folders simultaneously.
* 🔑 **Per-Folder Passwords:** Assign unique credentials to each directory.
* 🔁 **Brute-Force Protection:** Configurable maximum attempt limits.
* ⏳ **Timed Lockouts:** Automatic wait periods after failed attempts.
* 🖥️ **User-Friendly GUI:** Full Tkinter interface (no CLI knowledge required).
* 🔐 **AES/Fernet Encryption:** Industry-standard encrypted data storage.
* 🪟 **DPAPI Protection:** Encryption keys are protected by Windows DPAPI.
* 📁 **AppData Isolation:** Secure storage located in Windows AppData.
* 🎨 **Visual Feedback:** Real-time lock states with countdowns and color indicators.

---

## 🧠 How It Works (High-Level)

The application follows a tiered architecture to ensure data integrity and security:

1.  **GUI (Tkinter):** User interaction and folder selection.
2.  **Business Logic:** Manages attempts, timers, and state.
3.  **Encrypted Storage:** AES/Fernet layer for folder metadata.
4.  **Windows DPAPI:** User and machine-bound key protection.

* Folder metadata is encrypted on disk.
* The encryption key is **never stored in plaintext**.
* The key is protected by **Windows itself**.
* Data is strictly isolated per Windows user.

---

## 🔐 Security Design

### ✔ What This App Protects Against
* Casual access by other users.
* Curious coworkers or housemates.
* Accidental folder access/modification.
* Unauthorized copying of metadata to another machine.

### ❌ What This App Does NOT Protect Against
* Windows Administrators (System-level access).
* Disk removal or offline forensic attacks.
* Malicious system-level users.

> [!WARNING]  
> This app is designed for **personal privacy and workflow protection**, not administrator-level or military-grade security.

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

- [ ] Change password for existing locked folders.
- [ ] Dynamic handling of folder path changes.
- [ ] Windows Explorer integration (right-click to unlock).
- [ ] Audit logs for failed unlock attempts.
- [ ] Dark mode UI theme.
- [ ] System tray minimization.

