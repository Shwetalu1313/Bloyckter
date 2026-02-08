import winreg
import sys
import os

class RegistryService:
    @staticmethod
    def register_extension():
        
        "Registers the .bloyck files with this application in the Windows Registry."

        app_path = f'"{sys.executable}" "{os.path.abspath("main.py")}" --unlock "%1"'

        try:
            # create extension association
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.bloyck") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "BloyckterVault")

            # create shell command
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\BloyckterVault\shell\open\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, app_path)

            return True, "File extension .bloyck successfully registered."
        except Exception as e:
            return False, f"Failed to register .bloyck extension: {e}"
