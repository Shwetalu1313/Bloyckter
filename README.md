# Bloyckter - Secure Folder Vault + Workstation Lock

Bloyckter is a Windows desktop security utility built with Tkinter.
It provides:

- Encrypted folder vaulting (`.bloyck` containers)
- Per-folder password protection with lockout rules
- Workstation lock utility (manual lock + idle auto-lock)
- Remote mount locking support (Windows UNC/mapped drives + NFS/SMB mount points)

## Core Security Model

- Folder metadata is encrypted in `%LOCALAPPDATA%\Bloyckter\data.enc`.
- Encryption keys are protected with Windows DPAPI (`key.blob`).
- Passwords are hashed with PBKDF2-HMAC-SHA256 + per-folder salt.
- Lockout policy is enforced per vault item (`max_attempts`, `wait_time`).

## New Market-Ready Improvements

- Atomic encrypted data writes with backup fallback (`data.enc.bak`)
- Audit logging with log rotation (`audit.log`)
- Safer input validation in security dialogs
- Reliable restore-to-original-folder path when unlocking archives
- Isolated temporary extraction directories for quick-view unlocks
- Persistent workstation auto-lock settings (`settings.json`)

## Project Structure

- `main.py` - app entrypoint + CLI flags
- `app/ui/` - main GUI + dialogs
- `app/core/` - hashing, security, vault protection
- `app/data/` - encrypted data and settings repositories
- `app/services/` - OS integrations (registry, extraction, audit, workstation lock)

## Requirements

- Windows 10/11
- Python 3.10+
- Packages in `requirements.txt`:
  - `cryptography`
  - `pywin32`

Install:

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Workstation Lock Utility

From the GUI:

- Click `Lock Session Now` to lock Windows immediately.
- Enable `Idle auto-lock`, set idle minutes, and apply settings.
- Use `Mini Console Portal` to open a popup console for remote checks and command-driven locking.

From CLI:

```powershell
python main.py --lock-workstation
```

## Quick Unlock Flow

`.bloyck` files can be opened with:

```powershell
python main.py --unlock "C:\path\to\vault.bloyck"
```

If file association registration is available, double-clicking `.bloyck` files opens the quick unlock dialog.

## Mini Console Commands

Open the popup via the sidebar button `Open Console Portal`:

- `help`
- `test <path>`
- `lock <path> --password <pwd> [--cover <name>] [--attempts <1-10>] [--wait <15-86400>] [--visible]`

Example:

```powershell
lock "\\nas01\finance-share" --password "StrongPass123!" --cover "PrinterDriverCache"
```

## Important Limitations

- DPAPI ties vault decryption to the current Windows user and machine.
- Administrators with sufficient privileges can still access raw disk data.
- Losing both `data.enc` and `key.blob` means vault metadata cannot be recovered.

## Local Data Paths

Stored under `%LOCALAPPDATA%\Bloyckter`:

- `data.enc` - encrypted vault metadata
- `data.enc.bak` - backup of prior metadata
- `key.blob` - DPAPI-protected encryption key
- `settings.json` - workstation lock preferences
- `audit.log` - security event log
