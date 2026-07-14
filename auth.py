"""
Authentication module for the SAP BI Streamlit app.

Replaces the old plaintext-password check in data/users.json with bcrypt-hashed
credentials + per-user role. All verification is constant-time via bcrypt.checkpw.

Usage in app.py:
    from auth import verify_credentials, hash_password

    ok, role = verify_credentials(username, password)
    if not ok:
        st.error("بيانات الدخول غير صحيحة")
        st.stop()

Storage format for data/users.json (after running migrate_users.py once):
    {
      "maen": {
        "password_hash": "$2b$12$...",
        "role": "admin"
      },
      "rep1": {
        "password_hash": "$2b$12$...",
        "role": "user",
        "display_name": "Ahmed"
      }
    }

Notes:
- bcrypt cost is 12 (≈250ms on a typical server). Bump if you have hardware headroom.
- Passwords are never logged, never echoed, never written to disk in plaintext.
- This module never imports streamlit — it's pure Python so it can be unit tested.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import bcrypt

log = logging.getLogger(__name__)

# Default location; overridable via env so tests / CI don't have to touch real data.
USERS_FILE = Path(os.environ.get("SAP_USERS_FILE", "data/users.json"))
BCRYPT_ROUNDS = int(os.environ.get("SAP_BCRYPT_ROUNDS", "12"))


def _read_users(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.error("users.json is malformed: %s", exc)
        return {}


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt with a fresh random salt."""
    if not plain:
        raise ValueError("password must be non-empty")
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    ).decode("utf-8")


def verify_credentials(username: str, password: str) -> Tuple[bool, Optional[str], list]:
    """
    Verify (username, password) against data/users.json.
    Returns (ok, role). If not ok, role is None.

    bcrypt.checkpw is constant-time relative to the stored hash length, which
    defeats the classic "sub-millisecond difference between 'match' and 'no match'"
    side-channel. We further pin to a dummy hash on a missing user so the time
    to reject a non-existent username matches the time to reject a wrong
    password for an existing user.
    """
    users = _read_users(USERS_FILE)
    record = users.get(username)

    # Dummy hash cost-matches a real one so timing doesn't leak account existence.
    DUMMY = b"$2b$12$CwTycUXWue0Thq9StjUM0uJ8d8X8XJZ8oZ8oZ8oZ8oZ8oZ8oZ8oZ8o"

    if record is None or "password_hash" not in record:
        bcrypt.checkpw(password.encode("utf-8"), DUMMY)  # burn the time
        return False, None, []

    stored_hash = record["password_hash"].encode("utf-8")
    ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash)
    if not ok:
        return False, None, []
    return True, record.get("role", "user"), record.get("allowed_pages", ["all"])


def create_or_update_user(
    username: str,
    password: str,
    role: str = "user",
    **extra,
) -> dict:
    """
    Add or replace a user record. Hashes the password; never writes plaintext.
    Used by admin tooling and by the migration script.
    """
    if not username or not isinstance(username, str):
        raise ValueError("username must be a non-empty string")
    if role not in {"admin", "user"}:
        raise ValueError(f"role must be 'admin' or 'user', got {role!r}")

    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    users = _read_users(USERS_FILE)
    record = {"password_hash": hash_password(password), "role": role}
    record.update(extra)
    users[username] = record
    USERS_FILE.write_text(
        json.dumps(users, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info("wrote user record for %s (role=%s)", username, role)
    return record


__all__ = [
    "verify_credentials",
    "hash_password",
    "create_or_update_user",
    "USERS_FILE",
    "BCRYPT_ROUNDS",
]
