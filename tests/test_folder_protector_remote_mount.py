import os
import sys
import unittest
from unittest.mock import patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.protector.folder import FolderProtector
from app.data.models import FolderLock


class FolderProtectorRemoteMountTests(unittest.TestCase):
    @patch("app.core.protector.folder.AuditService.record")
    @patch("app.core.protector.folder.save_data")
    @patch("app.core.protector.folder.load_data", return_value={})
    @patch("app.core.protector.folder.SecurityService.restrict_permission")
    @patch("app.core.protector.folder.os.makedirs")
    @patch("app.core.protector.folder.is_remote_mount_root", return_value=True)
    @patch("app.core.protector.folder.is_remote_mount_path", return_value=True)
    @patch("app.core.protector.folder.ArchiveProtector.lock")
    @patch("app.core.protector.folder.os.path.exists")
    def test_lock_remote_mount_root_uses_local_vault_storage(
        self,
        exists_mock,
        archive_lock_mock,
        _is_remote_mock,
        _is_remote_root_mock,
        _makedirs_mock,
        restrict_permission_mock,
        _load_data_mock,
        save_data_mock,
        _audit_mock,
    ):
        source_path = r"\\nas01\shared"
        normalized_source = os.path.abspath(source_path)

        def fake_exists(path):
            return os.path.abspath(path) == normalized_source

        exists_mock.side_effect = fake_exists

        def fake_archive_lock(folder, **kwargs):
            folder.locked_path = kwargs["target_vault"]
            return True, "ok"

        archive_lock_mock.side_effect = fake_archive_lock

        folder = FolderLock(
            path=source_path,
            password_hash="hash",
            password_salt="salt",
            max_attempts=3,
            wait_time=120,
            cover_name="RemoteSecure",
            is_invisible=True,
        )

        success, _msg = FolderProtector().lock(folder)

        self.assertTrue(success)
        self.assertTrue(folder.is_remote_mount)
        archive_lock_mock.assert_called_once()

        _args, kwargs = archive_lock_mock.call_args
        self.assertTrue(kwargs.get("preserve_source_root"))
        self.assertIn("remote_vaults", kwargs.get("target_vault", ""))
        self.assertTrue(kwargs.get("target_vault", "").endswith(".bloyck"))

        restrict_permission_mock.assert_called_once_with(kwargs["target_vault"])
        save_data_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
