# BOT_TOKEN = "8390028953:AAHgptFi9rlIbNDHT4aNBsyf-E5wsmIAcQM"

import os

def _env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {name}")
    return v

# برای SQLite روی Render بهتره یک مسیر ثابت داشته باشی (اگر Persistent Disk داری، مسیرش رو اینجا بذار)
DB_PATH = os.getenv("DB_PATH", "app.db")

# Origins مجاز برای CORS (GitHub Pages)
# مثال: https://abouzarnameh.github.io
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()]
