import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.services.mini_console_service import MiniConsoleService


class MiniConsoleServiceTests(unittest.TestCase):
    def test_help_command(self):
        service = MiniConsoleService(lock_callback=lambda *_: (True, "ok"), connection_tester=lambda *_: (True, "ok"))
        success, message = service.execute("help")
        self.assertTrue(success)
        self.assertIn("Commands:", message)

    def test_test_command_calls_connection_tester(self):
        captured = {}

        def tester(path: str):
            captured["path"] = path
            return True, "reachable"

        service = MiniConsoleService(lock_callback=lambda *_: (True, "ok"), connection_tester=tester)
        success, message = service.execute('test "\\\\nas01\\shared\\folder"')
        self.assertTrue(success)
        self.assertEqual(message, "reachable")
        self.assertEqual(captured["path"], r"\\nas01\shared\folder")

    def test_lock_command_with_defaults(self):
        captured = {}

        def lock_cb(path, password, attempts, wait, cover, is_invisible):
            captured.update(
                {
                    "path": path,
                    "password": password,
                    "attempts": attempts,
                    "wait": wait,
                    "cover": cover,
                    "is_invisible": is_invisible,
                }
            )
            return True, "locked"

        service = MiniConsoleService(lock_callback=lock_cb, connection_tester=lambda *_: (True, "ok"))
        success, message = service.execute('lock "\\\\nas01\\shared" --password strongpass')
        self.assertTrue(success)
        self.assertEqual(message, "locked")
        self.assertEqual(captured["path"], r"\\nas01\shared")
        self.assertEqual(captured["password"], "strongpass")
        self.assertEqual(captured["attempts"], 3)
        self.assertEqual(captured["wait"], 180)
        self.assertTrue(captured["is_invisible"])

    def test_lock_requires_password(self):
        service = MiniConsoleService(lock_callback=lambda *_: (True, "ok"), connection_tester=lambda *_: (True, "ok"))
        success, message = service.execute('lock "\\\\nas01\\shared"')
        self.assertFalse(success)
        self.assertIn("--password is required", message)

    def test_lock_visible_flag(self):
        captured = {}

        def lock_cb(path, password, attempts, wait, cover, is_invisible):
            captured["is_invisible"] = is_invisible
            return True, "locked"

        service = MiniConsoleService(lock_callback=lock_cb, connection_tester=lambda *_: (True, "ok"))
        success, _message = service.execute('lock "\\\\nas01\\shared" --password strongpass --visible')
        self.assertTrue(success)
        self.assertFalse(captured["is_invisible"])


if __name__ == "__main__":
    unittest.main()
