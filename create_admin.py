"""
Create an admin account for QuizNest.

There is no public "Admin Register" page on purpose — admin accounts are
created from the command line so random visitors can't sign themselves up
as an admin. Run this once per admin you need.

Usage:
    python create_admin.py
"""

import getpass
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "quiz_system.db"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_users_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    existing_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)")]
    if "is_admin" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
    conn.commit()


def main():
    print("=== Create QuizNest Admin Account ===\n")

    full_name = input("Full name: ").strip()
    while not full_name:
        full_name = input("Full name (required): ").strip()

    email = input("Email: ").strip().lower()
    while not EMAIL_RE.match(email):
        email = input("Please enter a valid email: ").strip().lower()

    password = getpass.getpass("Password (min 6 characters): ")
    while len(password) < 6:
        password = getpass.getpass("Password too short, try again (min 6 characters): ")

    confirm = getpass.getpass("Confirm password: ")
    while confirm != password:
        confirm = getpass.getpass("Passwords don't match, confirm again: ")

    conn = get_db()
    ensure_users_table(conn)

    existing = conn.execute("SELECT id, is_admin FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        if existing["is_admin"]:
            print(f"\nAn admin account already exists for {email}.")
        else:
            promote = input(
                f"\nA student account already exists for {email}. Promote it to admin? [y/N]: "
            ).strip().lower()
            if promote == "y":
                conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (existing["id"],))
                conn.commit()
                print(f"\n{email} has been promoted to admin.")
            else:
                print("\nNo changes made.")
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (full_name, email, password_hash, is_admin, created_at) VALUES (?, ?, ?, 1, ?)",
        (full_name, email, generate_password_hash(password), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()

    print(f"\nAdmin account created for {full_name} ({email}).")
    print("You can now log in at /admin/login")


if __name__ == "__main__":
    main()
