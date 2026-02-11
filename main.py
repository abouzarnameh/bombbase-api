import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS
from db import init_db, get_conn
from models import PendingSimpleReq, AddItemReq

app = FastAPI(title="Bomb Base Sync API")

# CORS برای GitHub Pages / Mini App
# اگر ALLOWED_ORIGINS="*" گذاشتی، همه مجاز می‌شن (برای تست خوبه، برای نهایی محدودش کن)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

# 1) create/get pending session for creator_id
@app.post("/session/pending_simple")
def get_or_create_pending_simple(req: PendingSimpleReq):
    now = int(time.time() * 1000)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
      SELECT id FROM sessions
      WHERE creator_id=? AND status='pending'
      ORDER BY id DESC LIMIT 1
    """, (req.creator_id,))
    row = cur.fetchone()

    if row:
        sid = row["id"]
        conn.close()
        return {"sid": sid}

    cur.execute("""
      INSERT INTO sessions (creator_id, status, created_at_ms)
      VALUES (?, 'pending', ?)
    """, (req.creator_id, now))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return {"sid": sid}

# 2) get session + items
@app.get("/session")
def get_session(sid: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM sessions WHERE id=?", (sid,))
    s = cur.fetchone()
    if not s:
        conn.close()
        return {"error": "not_found"}

    cur.execute("""
      SELECT * FROM items
      WHERE session_id=?
      ORDER BY priority ASC, id ASC
    """, (sid,))
    items = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {"session": dict(s), "items": items}

# 3) add item
@app.post("/session/{sid}/add")
def add_item(sid: int, req: AddItemReq):
    now = int(time.time() * 1000)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM sessions WHERE id=?", (sid,))
    s = cur.fetchone()
    if not s:
        conn.close()
        return {"error": "not_found"}
    if s["status"] != "pending":
        conn.close()
        return {"error": "session_not_pending"}

    cur.execute("""
      INSERT INTO items (session_id, title, travel_ms, priority, created_at_ms)
      VALUES (?, ?, ?, ?, ?)
    """, (sid, req.title, req.travel_ms, req.priority, now))
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return {"ok": True, "item_id": item_id}

# 4) delete one item
@app.delete("/session/{sid}/item/{item_id}")
def delete_item(sid: int, item_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM sessions WHERE id=?", (sid,))
    if not cur.fetchone():
        conn.close()
        return {"error": "not_found"}

    cur.execute("DELETE FROM items WHERE id=? AND session_id=?", (item_id, sid))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return {"ok": True, "deleted": deleted}

# 5) delete whole session (and its items)
@app.delete("/session/{sid}")
def delete_session(sid: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM sessions WHERE id=?", (sid,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return {"ok": True, "deleted": deleted}
