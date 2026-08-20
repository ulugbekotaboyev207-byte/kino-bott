import sqlite3
from contextlib import contextmanager

DB_NAME = "videos.db"


def init_db():
    """Bazani va kerakli jadvalni yaratadi (agar mavjud bo'lmasa)."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                number TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    finally:
        conn.close()


def add_video(number: str, file_id: str):
    """Raqam va videoning file_id sini bazaga saqlaydi (mavjud bo'lsa yangilaydi)."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO videos (number, file_id) VALUES (?, ?) "
            "ON CONFLICT(number) DO UPDATE SET file_id = excluded.file_id",
            (number, file_id),
        )
        conn.commit()


def get_video(number: str):
    """Raqam bo'yicha video file_id sini qaytaradi, topilmasa None."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT file_id FROM videos WHERE number = ?", (number,))
        row = cursor.fetchone()
        return row[0] if row else None


def delete_video(number: str) -> bool:
    """Raqamni bazadan o'chiradi. Muvaffaqiyatli bo'lsa True qaytaradi."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM videos WHERE number = ?", (number,))
        conn.commit()
        return cursor.rowcount > 0


def list_all():
    """Barcha saqlangan raqamlar ro'yxatini qaytaradi."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT number, added_at FROM videos ORDER BY CAST(number AS INTEGER)")
        return cursor.fetchall()


def count_videos() -> int:
    with get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM videos")
        return cursor.fetchone()[0]
