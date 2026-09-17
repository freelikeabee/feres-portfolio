"""
Simple SQLite storage for the photo-unlock bot.

Tables:
  photos      -> the catalog of sellable photos
  purchases   -> records which user unlocked which photo
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "bot.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT NOT NULL,
                added_by INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS purchases (
                user_id INTEGER NOT NULL,
                photo_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, photo_id)
            )
            """
        )


def add_photo(file_id: str, price: int, description: str, added_by: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO photos (file_id, price, description, added_by) VALUES (?, ?, ?, ?)",
            (file_id, price, description, added_by),
        )
        return cur.lastrowid


def get_photo(photo_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
        return dict(row) if row else None


def list_all_photos():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM photos ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def list_unpurchased_photos(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM photos
            WHERE id NOT IN (
                SELECT photo_id FROM purchases WHERE user_id = ?
            )
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_purchased_photos(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.* FROM photos p
            JOIN purchases pu ON pu.photo_id = p.id
            WHERE pu.user_id = ?
            ORDER BY p.id
            """,
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def has_purchased(user_id: int, photo_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM purchases WHERE user_id = ? AND photo_id = ?",
            (user_id, photo_id),
        ).fetchone()
        return row is not None


def record_purchase(user_id: int, photo_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO purchases (user_id, photo_id) VALUES (?, ?)",
            (user_id, photo_id),
        )


def delete_photo(photo_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        conn.execute("DELETE FROM purchases WHERE photo_id = ?", (photo_id,))
