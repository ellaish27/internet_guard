"""SQLite storage: users (admin/superadmin), vouchers, sessions."""
from __future__ import annotations
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / ".internetguard" / "guard.db"
VOUCHER_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# Seeded on first run only. Change this immediately after setup --
# see admin_panel.py "Change password".
DEFAULT_SUPERADMIN_USERNAME = "su"
DEFAULT_SUPERADMIN_PASSWORD = "su2026"

ROLE_ADMIN = "admin"
ROLE_SUPERADMIN = "superadmin"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'superadmin')),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS vouchers (
                code TEXT PRIMARY KEY,
                duration_minutes INTEGER NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                used_at TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voucher_code TEXT NOT NULL,
                started_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ended_at TEXT
            );
        """)
        row = conn.execute("SELECT id FROM users WHERE role = 'superadmin'").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users(username, password_hash, role, created_at) "
                "VALUES (?, ?, 'superadmin', ?)",
                (
                    DEFAULT_SUPERADMIN_USERNAME,
                    _hash_password(DEFAULT_SUPERADMIN_PASSWORD),
                    datetime.now().isoformat(),
                )
            )


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- users --

def verify_user(username: str, password: str) -> dict | None:
    """Returns the user row (as dict) if credentials are correct, else None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
    if row is None or row["password_hash"] != _hash_password(password):
        return None
    return dict(row)


def create_user(username: str, password: str, role: str) -> tuple[bool, str]:
    """Creates a new admin/superadmin account. Returns (success, message)."""
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required."
    if role not in (ROLE_ADMIN, ROLE_SUPERADMIN):
        return False, "Invalid role."
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users(username, password_hash, role, created_at) "
                "VALUES (?, ?, ?, ?)",
                (username, _hash_password(password), role, datetime.now().isoformat())
            )
        return True, "Account created."
    except sqlite3.IntegrityError:
        return False, "That username already exists."


def delete_user(username: str) -> tuple[bool, str]:
    """Deletes any account. Superadmin-only -- enforce that check in the UI
    layer before calling this."""
    with _connect() as conn:
        # Never allow deleting the last remaining superadmin -- that would
        # lock everyone out permanently.
        row = conn.execute(
            "SELECT role FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            return False, "No such account."
        if row["role"] == ROLE_SUPERADMIN:
            count = conn.execute(
                "SELECT COUNT(*) AS n FROM users WHERE role = 'superadmin'"
            ).fetchone()["n"]
            if count <= 1:
                return False, "Cannot delete the last remaining superadmin."
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
    return True, "Account deleted."


def set_password(username: str, new_password: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (_hash_password(new_password), username)
        )


def list_users() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT username, role, created_at FROM users ORDER BY role, username"
        ).fetchall()
    return [dict(r) for r in rows]


# -------------------------------------------------------------- vouchers --

def generate_voucher(duration_minutes: int, created_by: str) -> str:
    code = "-".join(
        "".join(secrets.choice(VOUCHER_ALPHABET) for _ in range(4))
        for _ in range(3)
    )
    with _connect() as conn:
        conn.execute(
            "INSERT INTO vouchers(code, duration_minutes, created_by, created_at) "
            "VALUES (?, ?, ?, ?)",
            (code, duration_minutes, created_by, datetime.now().isoformat())
        )
    return code


def redeem_voucher(code: str) -> tuple[bool, int]:
    code = code.strip().upper()
    with _connect() as conn:
        row = conn.execute(
            "SELECT duration_minutes, used FROM vouchers WHERE code = ?", (code,)
        ).fetchone()
        if row is None or row["used"]:
            return False, 0
        conn.execute(
            "UPDATE vouchers SET used = 1, used_at = ? WHERE code = ?",
            (datetime.now().isoformat(), code)
        )
        return True, int(row["duration_minutes"])


def list_vouchers(created_by: str | None = None, limit: int = 20) -> list[dict]:
    """If created_by is given, only that admin's vouchers are returned.
    Superadmin panel calls this with created_by=None to see everything."""
    with _connect() as conn:
        if created_by is None:
            rows = conn.execute(
                "SELECT * FROM vouchers ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM vouchers WHERE created_by = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (created_by, limit)
            ).fetchall()
    return [dict(r) for r in rows]


# -------------------------------------------------------------- sessions --

def create_session(voucher_code: str, duration_minutes: int) -> int:
    started = datetime.now()
    expires = started + timedelta(minutes=duration_minutes)
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO sessions(voucher_code, started_at, expires_at) VALUES (?, ?, ?)",
            (voucher_code, started.isoformat(), expires.isoformat())
        )
        return int(cur.lastrowid)


def get_active_session() -> dict | None:
    now = datetime.now().isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE ended_at IS NULL AND expires_at > ? "
            "ORDER BY id DESC LIMIT 1",
            (now,)
        ).fetchone()
    return dict(row) if row else None


def end_session(session_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ?",
            (datetime.now().isoformat(), session_id)
        )


def end_expired_sessions() -> None:
    now = datetime.now().isoformat()
    with _connect() as conn:
        conn.execute(
            "UPDATE sessions SET ended_at = ? WHERE ended_at IS NULL AND expires_at <= ?",
            (now, now)
        )
