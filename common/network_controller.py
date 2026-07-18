"""Firewall control via `netsh advfirewall`."""
from __future__ import annotations
import ctypes
import subprocess

RULE_NAME = "Microsoft Internet Service 2026 (MIS-26)"


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _netsh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["netsh", "advfirewall", "firewall", *args],
        capture_output=True, text=True, timeout=15
    )


def is_blocked() -> bool:
    result = _netsh("show", "rule", f"name={RULE_NAME}")
    return "No rules match" not in result.stdout


def block_internet() -> None:
    _netsh("delete", "rule", f"name={RULE_NAME}")
    _netsh(
        "add", "rule", f"name={RULE_NAME}",
        "dir=out", "action=block", "enable=yes", "profile=any"
    )


def unblock_internet() -> None:
    _netsh("delete", "rule", f"name={RULE_NAME}")
