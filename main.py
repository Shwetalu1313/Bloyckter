import tkinter as tk
import sys
from app.ui.main_window import FolderLockerApp
from app.ui.dialogs.quick_unlock import QuickUnlockDialog
from app.services.registry_service import RegistryService

def main():

    # Initialize the registry keys on first run
    RegistryService.register_extension()

    # check if we were launched with doucblee-clicking a file
    if len(sys.argv) > 2 and sys.argv[1] == "--unlock":
        target_file = sys.argv[2]
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