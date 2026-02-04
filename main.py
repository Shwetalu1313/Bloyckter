import tkinter as tk
from app.ui.main_window import FolderLockerApp

def main():
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