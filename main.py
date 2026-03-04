import tkinter as tk
import sys
import argparse
from app.ui.main_window import FolderLockerApp
from app.ui.dialogs.quick_unlock import QuickUnlockDialog
from app.services.registry_service import RegistryService
from app.services.workstation_lock_service import lock_workstation
from app.services.audit_service import AuditService


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Bloyckter secure vault utility.")
    parser.add_argument("--unlock", dest="unlock_path", help="Open quick unlock dialog for a .bloyck file.")
    parser.add_argument("--lock-workstation", action="store_true", help="Lock the current Windows session.")
    return parser.parse_args(argv)

def main():
    args = parse_args(sys.argv[1:])

    # Initialize the registry keys on first run
    RegistryService.register_extension()

    if args.lock_workstation:
        success = lock_workstation()
        if success:
            AuditService.record("WORKSTATION_LOCKED", "trigger=cli_flag")
        else:
            AuditService.record_error("WORKSTATION_LOCK_FAILED", "trigger=cli_flag")
        return

    # check if we were launched with double-clicking a .bloyck file
    if args.unlock_path:
        target_file = args.unlock_path
        root = tk.Tk()

        # Show the quick unlock dialog
        QuickUnlockDialog(root, target_file)
        root.mainloop()
    else:
        """
        Main entry point for Bloyckter.
        Initializes the Tkinter root and the Object-Oriented GUI.
        """
        root = tk.Tk()
        
        # Initialize the app. Note: In a larger app, you might 
        # initialize your background services (VaultService) here first.
        app = FolderLockerApp(root)
        
        # Start the application loop
        root.mainloop()

if __name__ == "__main__":
    main()
