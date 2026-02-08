# 🔐 Bloyckter — Python Folder Locker (GUI)

Bloyckter is a Windows desktop application (Tkinter) that secures folders with per-folder passwords, configurable attempt limits, and timed lockouts. It stores folder metadata encrypted with AES (Fernet) and protects the encryption key using Windows DPAPI.

This README has been updated to reflect recent refactoring and enhancements: package layout, DPAPI-protected key handling, PBKDF2-based password hashing with per-folder salt, and a security service that centralizes lockout logic.

---

## ✨ Key Features (Updated)

- 🔒 Lock multiple folders
- 🕶 Cover-name obfuscation: folders are renamed to a generated cover name (hidden + system attributes) for extra obscurity
- 🔑 Unique password per folder with PBKDF2-HMAC-SHA256 and per-folder salt
- 🔁 Configurable maximum failed attempts and automated cooldown/lockout handling
- 🛡 SecurityService: central handling of failed attempts, lockout timers, and state persistence
- 🔐 Encrypted local storage (`data.enc`) with AES/Fernet
- 🪟 DPAPI-protected key (`key.blob`) bound to the current Windows user and machine
- 🗂 App packaged under `app/` with clear separation: `ui`, `core`, `data` modules
- 🖥️ Tkinter GUI with visual countdown and color indicators for lockout state
- 🔑 Change password without unlocking (supported)

---

## Project Layout (high-level)

- `main.py` — Application entry point
- `app/ui/` — GUI components and windows
- `app/core/` — Core logic (protector implementations, hashing, security)
- `app/data/` — Encrypted repository, data models, persistence helpers
- `helper.py` — Low-level helpers used by legacy modules (kept for compatibility)

---

## How It Works (concise)

- The GUI delegates operations to `FolderProtector` implementations in `app.core.protector`.
- Passwords are hashed with PBKDF2 using a unique salt per folder.
- Metadata is serialized and encrypted with Fernet; the key is stored protected by DPAPI so it can only be unprotected by the same Windows user on the same machine.
- `SecurityService` manages failed attempt counting and sets `locked_until` timestamps; the GUI shows remaining wait time when applicable.

---

## Requirements

- Windows 10/11
- Python 3.10+
- Packages (see `requirements.txt`): `cryptography`, `pywin32`, `tk` (part of standard lib)

Install dependencies in the project virtualenv:

```powershell
python -m pip install -r requirements.txt
```

---

## Run the App

From project root with your venv activated:

```powershell
python main.py
```

Note: `main.py` launches the packaged app (`app/`) and ensures imports resolve correctly.

---

## Recovering / Manually Unlocking Folders

- Bloyckter stores metadata in `%LOCALAPPDATA%\Bloyckter` as `data.enc` and the DPAPI-protected key as `key.blob`.
- If you still have the original password, use the app's Unlock flow. If the app cannot unlock (metadata missing/corrupt) you can manually remove the Hidden/System attributes and rename the folder back to its original name (see the `attrib` and `rename` commands). Always back up `data.enc` and `key.blob` before attempting recovery.

---

## Notes & Limitations

- DPAPI binds the key to the Windows user and machine — copying `key.blob` to another machine or user will prevent decryption.
- Administrators can still access files if they have sufficient privileges.
- Deleting `data.enc` or `key.blob` results in permanent loss of metadata (locked folders cannot be restored by the app without them).

---

## Recent Enhancements

- Refactored to `app/` package with modular `core`, `ui`, and `data` layers.
- Added `FolderProtector` abstraction and cover-name obfuscation.
- Centralized security rules in `SecurityService` for consistent lockout behavior.
- Improved PBKDF2 hashing and salt handling.
- Robust DPAPI handling with compatibility fixes for different `pywin32` versions.

---

## Comming Features
[] app settings where user can configure itself
[] After Unlocking the folder, folder is coming back with the cover_name. it should come with original name.
[] blyock is only clickable one time. after one time, terminal is showing very quickly and fired.
[] we need to combine with original timer and attempt function to the blyock file extension.

