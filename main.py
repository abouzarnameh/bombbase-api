# main.py
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from db import init_db, get_conn

app = FastAPI()

# CORS (از env هم می‌تونی ست کنی)
origins_env = os.getenv("ALLOWED_ORIGINS", "https://abouzarnameh.github.io")
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

# ---------- Models ----------
class PendingSimpleReq(BaseModel):
    creator_id: int

class AddItemReq(BaseModel):
    title: Optional[str] = None
    travel_ms: int = Field(ge=1)
    priority: int = Field(default=1, ge=1)

class StartReq(BaseModel):
    user_id: int

# ---------- Endpoints ----------
@app.post("/session/pending_simple")
def create_or_get_pending_simple(req: PendingSimpleReq):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
      SELECT id FROM sessions
      WHERE creator_id=? AND status='pending'
      ORDER BY id DESC LIMIT 1
    """, (req.creator_id,))
    row = cur.fetchone()
    if row:
        conn.close()
        return {"sid": row["id"]}

    now = int(time.time() * 1000)
    cur.execute("""
      INSERT INTO sessions (creator_id, status, created_at_ms)
      VALUES (?, 'pending', ?)
    """, (req.creator_id, now))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return {"sid": sid}

@app.get("/session")
def get_session(sid: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
      SELECT id, creator_id, status, created_at_ms, started_at_ms
      FROM sessions WHERE id=?
    """, (sid,))
    s = cur.fetchone()
    if not s:
        conn.close()
        return {"error": "not_found"}

    cur.execute("""
      SELECT id, title, travel_ms, priority, created_at_ms
      FROM items
      WHERE session_id=?
      ORDER BY id ASC
    """, (sid,))
    items = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {
        "session": dict(s),
        "items": items,
        "server_now_ms": int(time.time() * 1000)
    }

@app.post("/session/{sid}/add")
def add_item(sid: int, req: AddItemReq):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, status FROM sessions WHERE id=?", (sid,))
    s = cur.fetchone()
    if not s:
        conn.close()
        return {"error": "not_found"}
    if s["status"] != "pending":
        conn.close()
        return {"error": "session_not_pending"}

    now = int(time.time() * 1000)
    cur.execute("""
      INSERT INTO items (session_id, title, travel_ms, priority, created_at_ms)
      VALUES (?, ?, ?, ?, ?)
    """, (sid, req.title, req.travel_ms, req.priority, now))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/session/{sid}/item/{item_id}")
def delete_item(sid: int, item_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM sessions WHERE id=?", (sid,))
    s = cur.fetchone()
    if not s:
        conn.close()
        return {"error": "not_found"}

    cur.execute("DELETE FROM items WHERE id=? AND session_id=?", (item_id, sid))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/session/{sid}/start")
def start_session(sid: int, req: StartReq):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
      SELECT id, creator_id, status, started_at_ms
      FROM sessions WHERE id=?
    """, (sid,))
    s = cur.fetchone()
    if not s:
        conn.close()
        return {"error": "not_found"}

    # فقط سازنده سشن حق start دارد (برای امنیت واقعی)
    if int(req.user_id) != int(s["creator_id"]):
        conn.close()
        return {"error": "forbidden"}

    if s["status"] != "pending":
        # اگر قبلاً start شده یا running شده، همون started_at_ms رو بده
        conn.close()
        return {"ok": True, "started_at_ms": s["started_at_ms"]}

    cur.execute("SELECT COUNT(*) AS c FROM items WHERE session_id=?", (sid,))
    if cur.fetchone()["c"] == 0:
        conn.close()
        return {"error": "empty"}

    started = int(time.time() * 1000)
    cur.execute("""
      UPDATE sessions
      SET status='running', started_at_ms=?
      WHERE id=?
    """, (started, sid))
    conn.commit()
    conn.close()
    return {"ok": True, "started_at_ms": started}
