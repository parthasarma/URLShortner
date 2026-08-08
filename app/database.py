import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = "data/urls.db"

def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_url TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_urls_long_url ON urls(long_url)")
    conn.commit()

def get_url_by_long_url(conn: sqlite3.Connection, long_url: str):
    cur = conn.execute("SELECT id, long_url, created_at FROM urls WHERE long_url = ?", (long_url,))
    return cur.fetchone()

def get_url_by_id(conn: sqlite3.Connection, id: int):
    cur = conn.execute("SELECT id, long_url, created_at FROM urls WHERE id = ?", (id,))
    return cur.fetchone()

def insert_url(conn: sqlite3.Connection, long_url: str, created_at: str) -> int:
    cur = conn.execute(
        "INSERT INTO urls (long_url, created_at) VALUES (?, ?)",
        (long_url, created_at)
    )
    conn.commit()
    return cur.lastrowid

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
