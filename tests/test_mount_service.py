import os
import sys
import unittest
from unittest.mock import patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.services.mount_service import is_remote_mount_path, is_remote_mount_root


class MountServiceTests(unittest.TestCase):
    def test_unc_path_is_detected_as_remote(self):
        self.assertTrue(is_remote_mount_path(r"\\nas01\shared\vault"))

    def test_windows_mapped_drive_is_detected_as_remote(self):
        with patch("app.services.mount_service.os.name", "nt"), patch(
            "app.services.mount_service._is_windows_remote_drive", return_value=True
        ):
            self.assertTrue(is_remote_mount_path(r"Z:\team\vault"))

    def test_remote_mount_root_true_when_mount_and_remote(self):
        with patch("app.services.mount_service.os.path.ismount", return_value=True), patch(
            "app.services.mount_service.is_remote_mount_path", return_value=True
        ):
            self.assertTrue(is_remote_mount_root(r"Z:\\"))

    def test_remote_mount_root_false_when_not_mount(self):
        with patch("app.services.mount_service.os.path.ismount", return_value=False), patch(
            "app.services.mount_service.is_remote_mount_path", return_value=True
        ):
            self.assertFalse(is_remote_mount_root(r"Z:\\"))


if __name__ == "__main__":
    unittest.main()
