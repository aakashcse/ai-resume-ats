"""
A tiny user store using SQLite (built into Python, no server needed).

The first time someone signs in with Google, a row is created: that is their
"sign up". Every later sign-in updates `last_login_at`.

We only store what Google tells us and what we need to show: no passwords.
Google handles passwords and 2-factor authentication for us.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Dict, Tuple

from backend import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    google_id      TEXT PRIMARY KEY,   -- Google's stable user id (the token's "sub" claim)
    email          TEXT NOT NULL,
    name           TEXT,
    picture        TEXT,
    created_at     TEXT NOT NULL,
    last_login_at  TEXT NOT NULL
)
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def get_or_create_user(google_id: str, email: str, name: str = "", picture: str = "") -> Tuple[Dict, bool]:
    """Return (user, is_new_user). Creates the user on their first sign-in."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with _connect() as conn:  # "with" commits automatically
        row = conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()
        is_new = row is None

        if is_new:
            conn.execute(
                "INSERT INTO users (google_id, email, name, picture, created_at, last_login_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (google_id, email, name, picture, now, now),
            )
        else:
            # Keep name/picture up to date in case they changed them on Google.
            conn.execute(
                "UPDATE users SET email = ?, name = ?, picture = ?, last_login_at = ? WHERE google_id = ?",
                (email, name, picture, now, google_id),
            )

        user = dict(conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone())
    return user, is_new
