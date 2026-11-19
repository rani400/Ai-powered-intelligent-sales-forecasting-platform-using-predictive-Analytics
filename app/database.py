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

CONVERSATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 lead_id INTEGER,
 meeting_type TEXT NOT NULL DEFAULT 'Discovery Call',
 transcript TEXT NOT NULL,
 summary TEXT,
 key_points TEXT,
 customer_concerns TEXT,
 action_items TEXT,
 next_steps TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

ACTIVITIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS activities (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 lead_id INTEGER NOT NULL,
 activity_type TEXT NOT NULL DEFAULT 'note',
 subject TEXT NOT NULL DEFAULT '',
 body TEXT NOT NULL DEFAULT '',
 occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CRM_SYNC_LOGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS crm_sync_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 crm TEXT NOT NULL,
 entity_type TEXT NOT NULL,
 entity_id INTEGER,
 direction TEXT NOT NULL DEFAULT 'push',
 status TEXT NOT NULL DEFAULT 'pending',
 message TEXT NOT NULL DEFAULT '',
 payload TEXT,
 remote_id TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SALES_INTERACTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sales_interactions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 lead_id INTEGER,
 interaction_type TEXT NOT NULL DEFAULT 'call',
 title TEXT NOT NULL DEFAULT '',
 participants TEXT NOT NULL DEFAULT '',
 transcript TEXT NOT NULL,
 summary TEXT NOT NULL DEFAULT '',
 key_discussion_points TEXT NOT NULL DEFAULT '[]',
 action_items TEXT NOT NULL DEFAULT '[]',
 customer_concerns TEXT NOT NULL DEFAULT '[]',
 next_steps TEXT NOT NULL DEFAULT '[]',
 sentiment TEXT NOT NULL DEFAULT '',
 source TEXT NOT NULL DEFAULT 'rule-based',
 occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.executescript(CONVERSATIONS_SCHEMA)
        conn.executescript(ACTIVITIES_SCHEMA)
        conn.executescript(CRM_SYNC_LOGS_SCHEMA)
        conn.executescript(SALES_INTERACTIONS_SCHEMA)
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

def save_conversation(lead_id, meeting_type, transcript, summary, key_points, customer_concerns, action_items, next_steps):
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO conversations 
               (lead_id, meeting_type, transcript, summary, key_points, customer_concerns, action_items, next_steps)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (lead_id, meeting_type, transcript, summary, key_points, customer_concerns, action_items, next_steps))
        conn.commit()
        return cur.lastrowid

def save_interaction(lead_id, interaction_type, title, participants, transcript, summary,
                     key_discussion_points, action_items, customer_concerns, next_steps,
                     sentiment="", source="rule-based"):
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO sales_interactions
               (lead_id, interaction_type, title, participants, transcript, summary,
                key_discussion_points, action_items, customer_concerns, next_steps, sentiment, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (lead_id, interaction_type, title, participants, transcript, summary,
             key_discussion_points, action_items, customer_concerns, next_steps, sentiment, source))
        conn.commit()
        row = conn.execute("SELECT * FROM sales_interactions WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)

def list_interactions(lead_id=None, interaction_type=None, limit=100):
    sql, params = "SELECT * FROM sales_interactions WHERE 1=1", []
    if lead_id is not None:
        sql += " AND lead_id = ?"; params.append(lead_id)
    if interaction_type:
        sql += " AND interaction_type = ?"; params.append(interaction_type)
    sql += " ORDER BY id DESC LIMIT ?"; params.append(limit)
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

def get_interaction(interaction_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM sales_interactions WHERE id=?", (interaction_id,)).fetchone()
    return dict(row) if row else None

def delete_interaction(interaction_id):
    with connect() as conn:
        cur = conn.execute("DELETE FROM sales_interactions WHERE id=?", (interaction_id,))
    return cur.rowcount > 0
