import os
import io
import zipfile
import subprocess
import tempfile
from app.core.security.dpapi import get_cipher
from app.services.audit_service import AuditService

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
            
            # Extract to an isolated temp location to avoid collisions.
            temp_dir = tempfile.mkdtemp(prefix="Bloyckter_Temp_")
            
            with zipfile.ZipFile(io.BytesIO(decrypted_zip)) as zf:
                zf.extractall(temp_dir)
            
            # Open the folder for the user
            subprocess.run(f'explorer "{temp_dir}"')
            AuditService.record("TEMP_VIEW_OPENED", f"vault={vault_path} temp={temp_dir}")
            
            return True, "Vault opened in temporary view."
        except Exception as e:
            AuditService.record_error("TEMP_VIEW_FAILED", f"vault={vault_path} error={e}")
            return False, f"Decryption failed: {str(e)}"
