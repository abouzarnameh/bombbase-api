import sqlite3
from config import DB_PATH

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # sessions: یک pending برای هر creator
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      creator_id INTEGER NOT NULL,
      status TEXT NOT NULL,
      created_at_ms INTEGER NOT NULL
    );
    """)

    # items: travel_ms + priority + title
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id INTEGER NOT NULL,
      title TEXT,
      travel_ms INTEGER NOT NULL,
      priority INTEGER NOT NULL DEFAULT 1,
      created_at_ms INTEGER NOT NULL,
      FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    """)

    # برای اینکه FK عمل کنه
    cur.execute("PRAGMA foreign_keys=ON;")
    conn.commit()
    conn.close()
