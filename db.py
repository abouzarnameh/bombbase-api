# db.py
import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "app.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # sessions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at_ms INTEGER NOT NULL,
        started_at_ms INTEGER
    )
    """)

    # items
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        title TEXT,
        travel_ms INTEGER NOT NULL,
        priority INTEGER NOT NULL DEFAULT 1,
        created_at_ms INTEGER NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    """)

    # مهاجرت ساده اگر دیتابیس قدیمی بود
    cur.execute("PRAGMA table_info(sessions);")
    cols = [r["name"] for r in cur.fetchall()]
    if "started_at_ms" not in cols:
        cur.execute("ALTER TABLE sessions ADD COLUMN started_at_ms INTEGER;")

    cur.execute("PRAGMA table_info(items);")
    icols = [r["name"] for r in cur.fetchall()]
    if "travel_ms" not in icols and "duration_ms" in icols:
        # اگر قبلاً duration_ms داشتی، اینجا migrate کامل نمی‌کنیم چون sqlite rename column سخت‌تره
        # پیشنهاد: دیتابیس را ریست کنی یا migrate جدا بنویسیم.
        pass

    conn.commit()
    conn.close()
