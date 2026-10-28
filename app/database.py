import os, sqlite3
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH", "./data/salesgenie.db")
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 company_name TEXT NOT NULL,
 industry TEXT NOT NULL DEFAULT 'Unknown',
 contact_name TEXT NOT NULL DEFAULT 'there',
 contact_title TEXT NOT NULL DEFAULT '',
 email TEXT, phone TEXT,
 company_size INTEGER NOT NULL DEFAULT 0,
 engagement_score REAL NOT NULL DEFAULT 0,
 lead_status TEXT NOT NULL DEFAULT 'New',
 notes TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)
        # Migrate existing schema if needed
        cur = conn.execute("PRAGMA table_info(leads)")
        cols = {row[1] for row in cur.fetchall()}
        migrations = []
        if 'engagement_score' not in cols:
            migrations.append("ALTER TABLE leads ADD COLUMN engagement_score REAL NOT NULL DEFAULT 0")
        if 'annual_revenue' in cols:
            pass
        for m in migrations:
            try:
                conn.execute(m)
            except:
                pass

BOOL_FIELDS = set()
def row_to_dict(row):
    if row is None: return None
    result = dict(row)
    return result
