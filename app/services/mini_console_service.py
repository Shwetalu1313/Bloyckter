import os
import shlex
from typing import Callable


class MiniConsoleService:
    def __init__(
        self,
        lock_callback: Callable[[str, str, int, int, str, bool], tuple[bool, str]],
        connection_tester: Callable[[str], tuple[bool, str]],
    ):
        self.lock_callback = lock_callback
        self.connection_tester = connection_tester

    @staticmethod
    def help_text() -> str:
        return (
            "Commands:\n"
            "  help\n"
            "  test <path>\n"
            "  lock <path> --password <pwd> [--cover <name>] [--attempts <1-10>] "
            "[--wait <15-86400>] [--visible]"
        )

    def execute(self, command: str) -> tuple[bool, str]:
        raw = (command or "").strip()
        if not raw:
            return False, "No command provided. Type 'help' for usage."

        try:
            tokens = shlex.split(raw, posix=False)
        except ValueError as ex:
            return False, f"Invalid command syntax: {ex}"

        if not tokens:
            return False, "No command provided. Type 'help' for usage."

        cmd = tokens[0].lower()

        if cmd in {"help", "?"}:
            return True, self.help_text()
        if cmd == "test":
            return self._handle_test(tokens[1:])
        if cmd == "lock":
            return self._handle_lock(tokens[1:])

        return False, f"Unknown command '{tokens[0]}'. Type 'help' for usage."

    def _handle_test(self, args: list[str]) -> tuple[bool, str]:
        if not args:
            return False, "Usage: test <path>"
        path = " ".join(args).strip().strip('"')
        if not path:
            return False, "Usage: test <path>"
        return self.connection_tester(path)

    def _handle_lock(self, args: list[str]) -> tuple[bool, str]:
        if not args:
            return False, (
                "Usage: lock <path> --password <pwd> [--cover <name>] [--attempts <1-10>] "
                "[--wait <15-86400>] [--visible]"
            )

        path = args[0].strip().strip('"')
        if not path or path.startswith("-"):
            return False, "lock requires a path as the first argument."

        password = None
        cover = f"{os.path.basename(os.path.normpath(path)) or 'RemoteVault'}_vault"
        attempts = 3
        wait = 180
        is_invisible = True

        i = 1
        while i < len(args):
            flag = args[i].lower()
            if flag in {"--password", "-p"}:
                i += 1
                if i >= len(args):
                    return False, "Missing value for --password."
                password = args[i]
            elif flag in {"--cover", "-c"}:
                i += 1
                if i >= len(args):
                    return False, "Missing value for --cover."
                cover = args[i].strip().strip('"')
            elif flag in {"--attempts", "-a"}:
                i += 1
                if i >= len(args):
                    return False, "Missing value for --attempts."
                try:
                    attempts = int(args[i])
                except ValueError:
                    return False, "--attempts must be a number."
            elif flag in {"--wait", "-w"}:
                i += 1
                if i >= len(args):
                    return False, "Missing value for --wait."
                try:
                    wait = int(args[i])
                except ValueError:
                    return False, "--wait must be a number."
            elif flag == "--visible":
                is_invisible = False
            else:
                return False, f"Unknown option '{args[i]}'."
            i += 1

        if not password:
            return False, "--password is required."
        if attempts < 1 or attempts > 10:
            return False, "--attempts must be between 1 and 10."
        if wait < 15 or wait > 86400:
            return False, "--wait must be between 15 and 86400 seconds."
        if not cover:
            return False, "--cover cannot be empty."

        return self.lock_callback(path, password, attempts, wait, cover, is_invisible)
