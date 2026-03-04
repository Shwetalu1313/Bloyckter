import time
import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.services.workstation_lock_service import WorkstationLockService


class WorkstationLockServiceTests(unittest.TestCase):
    def test_monitor_triggers_lock_once(self):
        state = {"idle": 0.0, "calls": 0}

        def idle_provider():
            return state["idle"]

        def lock_action():
            state["calls"] += 1
            return True

        service = WorkstationLockService(
            check_interval_seconds=1,
            on_lock=None,
            idle_provider=idle_provider,
            lock_action=lock_action,
        )
        try:
            service.start(idle_threshold_seconds=30)
            state["idle"] = 45.0
            time.sleep(1.2)
            self.assertEqual(state["calls"], 1)

            # Stay idle above threshold; lock should not retrigger until reset.
            time.sleep(1.2)
            self.assertEqual(state["calls"], 1)
        finally:
            service.stop()

    def test_lock_now_uses_lock_action(self):
        calls = {"count": 0}

        def lock_action():
            calls["count"] += 1
            return True

        service = WorkstationLockService(lock_action=lock_action)
        success = service.lock_now()
        self.assertTrue(success)
        self.assertEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
