import os
import io
import zipfile
import subprocess
from app.core.security.dpapi import get_cipher

class ExtractionService:
    """
    Manages the temporary 'decrypted' view of your files.
    """

    @staticmethod
    def decrypt_and_open(vault_path: str):
        """
        Decrypts the vault into a temporary folder and opens it in Explorer.
        """
        try:
            cipher = get_cipher()
            
            with open(vault_path, "rb") as f:
                encrypted_content = f.read()
            
            # Decrypt the AES container
            decrypted_zip = cipher.decrypt(encrypted_content)
            
            # Extract to a temp location
            temp_dir = os.path.join(os.environ['TEMP'], "Bloyckter_Temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(io.BytesIO(decrypted_zip)) as zf:
                zf.extractall(temp_dir)
            
            # Open the folder for the user
            subprocess.run(f'explorer "{temp_dir}"')
            
            return True, "Vault opened in temporary view."
        except Exception as e:
            return False, f"Decryption failed: {str(e)}"