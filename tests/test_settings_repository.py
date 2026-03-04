import os
import sys
import unittest
from unittest.mock import mock_open, patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import app.data.settings_repository as settings_repository


class SettingsRepositoryTests(unittest.TestCase):
    def test_load_defaults_when_file_missing(self):
        with patch("app.data.settings_repository.os.path.exists", return_value=False):
            loaded = settings_repository.load_settings()
        self.assertFalse(loaded["workstation_auto_lock_enabled"])
        self.assertEqual(loaded["workstation_idle_minutes"], 10)

    def test_save_settings_normalizes_values(self):
        with patch("app.data.settings_repository._atomic_write_json") as atomic_write:
            settings_repository.save_settings(
                {
                    "workstation_auto_lock_enabled": 1,
                    "workstation_idle_minutes": "300",
                }
            )

        atomic_write.assert_called_once()
        args, _kwargs = atomic_write.call_args
        self.assertEqual(args[0], settings_repository.SETTINGS_FILE)
        self.assertTrue(args[1]["workstation_auto_lock_enabled"])
        self.assertEqual(args[1]["workstation_idle_minutes"], 240)

    def test_load_settings_merges_and_normalizes(self):
        payload = '{"workstation_auto_lock_enabled": true, "workstation_idle_minutes": -1}'
        with patch("app.data.settings_repository.os.path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=payload)
        ):
            loaded = settings_repository.load_settings()

        self.assertTrue(loaded["workstation_auto_lock_enabled"])
        self.assertEqual(loaded["workstation_idle_minutes"], 1)


if __name__ == "__main__":
    unittest.main()
