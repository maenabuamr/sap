"""
One-time migration: convert data/users.json from plaintext passwords to bcrypt hashes.

Run from project root:
    python migrate_users.py

What it does:
1. Reads data/users.json.
2. For each user record that has a "password" field (plaintext legacy format),
   computes a bcrypt hash and rewrites the record with "password_hash".
3. Writes a backup at data/users.json.bak.<timestamp> first.
4. Writes the new shape to data/users.json.

Safe to re-run — already-migrated records are left alone.
Idempotent: if every record already has "password_hash", the script is a no-op.

After running:
- DELETE the backup file (or move it outside the repo; it's plaintext).
- ROTATE every password at the next login, OR force-reset via the admin page.
- NEVER commit data/users.json again — see the new .gitignore.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Allow running this from project root or anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auth import USERS_FILE, create_or_update_user, hash_password  # noqa: E402


def main() -> int:
    if not USERS_FILE.exists():
        print(f"[skip] {USERS_FILE} does not exist — nothing to migrate.")
        print("       (this is fine for a fresh project; create users later via create_or_update_user.)")
        return 0

    raw = USERS_FILE.read_text(encoding="utf-8")
    try:
        users = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[fail] {USERS_FILE} is not valid JSON: {exc}")
        return 1

    if not isinstance(users, dict):
        print(f"[fail] {USERS_FILE} should be a JSON object keyed by username.")
        return 1

    # Detect whether any legacy plaintext records exist.
    legacy_keys = [u for u, r in users.items() if isinstance(r, dict) and "password" in r]
    if not legacy_keys:
        if all(isinstance(r, dict) and "password_hash" in r for r in users.values()):
            print(f"[ok] all {len(users)} users already use password_hash. No work to do.")
            return 0
        print("[warn] mixed records detected — some have 'password', some have 'password_hash'.")
        print("        Plaintext records will be upgraded; hashed ones left alone.")

    # Backup first.
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = USERS_FILE.with_suffix(f".json.bak.{ts}")
    backup.write_text(raw, encoding="utf-8")
    print(f"[backup] wrote {backup}")

    migrated = 0
    skipped = 0
    for username, record in users.items():
        if not isinstance(record, dict):
            print(f"[skip] {username}: record is not an object, leaving as-is.")
            skipped += 1
            continue
        if "password_hash" in record:
            skipped += 1
            continue
        if "password" not in record:
            print(f"[skip] {username}: no 'password' field present.")
            skipped += 1
            continue
        plaintext = record["password"]
        if not isinstance(plaintext, str) or not plaintext:
            print(f"[skip] {username}: empty or non-string plaintext, skipping.")
            skipped += 1
            continue
        role = record.get("role", "user")
        extras = {k: v for k, v in record.items() if k not in {"password", "role"}}
        create_or_update_user(username, plaintext, role=role, **extras)
        migrated += 1

    # After migration, remove plaintext password file from disk if it lingered
    # (we wrote a backup; the live file is now hashed-only).
    print(f"[done] migrated={migrated}, skipped={skipped}")
    print()
    print("Next steps:")
    print("  1. Verify you can log in to the app with one of the existing usernames.")
    print(f"  2. Delete or move {backup} OUT of the repo (it's still plaintext).")
    print(f"  3. Confirm .gitignore now excludes {USERS_FILE}.")
    print("  4. (Recommended) force a password change at next login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
