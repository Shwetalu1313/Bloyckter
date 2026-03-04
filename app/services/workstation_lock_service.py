import ctypes
import threading
import time
from ctypes import wintypes
from typing import Callable, Optional


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


def get_idle_seconds() -> Optional[float]:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)

    if not user32.GetLastInputInfo(ctypes.byref(last_input)):
        return None

    # GetTickCount wraps every ~49 days. This app's idle window is short, so
    # a wrap-around edge is acceptable and self-correcting.
    elapsed_ms = kernel32.GetTickCount() - last_input.dwTime
    if elapsed_ms < 0:
        return 0.0
    return elapsed_ms / 1000.0


def lock_workstation() -> bool:
    return bool(ctypes.windll.user32.LockWorkStation())


class WorkstationLockService:
    def __init__(
        self,
        check_interval_seconds: int = 5,
        on_lock: Optional[Callable[[], None]] = None,
        idle_provider: Callable[[], Optional[float]] = get_idle_seconds,
        lock_action: Callable[[], bool] = lock_workstation,
    ):
        self.check_interval_seconds = max(check_interval_seconds, 1)
        self.on_lock = on_lock
        self.idle_provider = idle_provider
        self.lock_action = lock_action
        self._thread = None
        self._stop_event = threading.Event()
        self._threshold_seconds = 0
        self._lock_triggered = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def lock_now(self, notify: bool = False) -> bool:
        success = self.lock_action()
        if success and notify and self.on_lock:
            self.on_lock()
        return success

    def start(self, idle_threshold_seconds: int):
        self.stop()
        self._threshold_seconds = max(int(idle_threshold_seconds), 30)
        self._lock_triggered = False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._thread = None
        self._lock_triggered = False

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            idle_seconds = self.idle_provider()
            if idle_seconds is not None:
                if idle_seconds >= self._threshold_seconds and not self._lock_triggered:
                    if self.lock_action():
                        self._lock_triggered = True
                        if self.on_lock:
                            self.on_lock()
                elif idle_seconds < min(10, self._threshold_seconds // 4):
                    self._lock_triggered = False
            time.sleep(self.check_interval_seconds)
