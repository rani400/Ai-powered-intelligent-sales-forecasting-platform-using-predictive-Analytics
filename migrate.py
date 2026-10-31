import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH", "./data/salesgenie.db")
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if leads table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
    if not cur.fetchone():
        print("No leads table found. Creating new schema...")
        conn.execute('''CREATE TABLE leads (
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
        )''')
        conn.commit()
        conn.close()
        print("New schema created successfully!")
        return
    
    # Get current columns
    cur.execute("PRAGMA table_info(leads)")
    cols = {row[1] for row in cur.fetchall()}
    print(f"Current columns: {cols}")
    
    # Check if migration needed
    old_cols = {'website_visits', 'email_opens', 'email_clicks', 'budget_confirmed', 'need_identified', 'decision_maker', 'annual_revenue'}
    if old_cols.intersection(cols) or 'engagement_score' not in cols or 'company_size' not in cols:
        print("Old schema detected. Migrating...")
        conn.execute('''CREATE TABLE leads_new (
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
        )''')
        
        engagement_expr = "COALESCE(engagement_score, 0)" if 'engagement_score' in cols else "0"
        conn.execute(f'''INSERT INTO leads_new (id, company_name, industry, contact_name, contact_title, email, phone, company_size, engagement_score, lead_status, notes, created_at, updated_at)
        SELECT id, 
               company_name, 
               COALESCE(industry, 'Unknown'), 
               COALESCE(contact_name, 'there'), 
               COALESCE(contact_title, ''), 
               email, 
               phone, 
               COALESCE(company_size, 0),
               {engagement_expr},
               COALESCE(lead_status, 'New'), 
               COALESCE(notes, ''),
               COALESCE(created_at, CURRENT_TIMESTAMP), 
               COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM leads''')
        
        conn.execute('DROP TABLE leads')
        conn.execute('ALTER TABLE leads_new RENAME TO leads')
        conn.commit()
        print("Migration completed successfully!")
    else:
        print("Schema is up to date. No migration needed.")
    
    conn.close()

if __name__ == '__main__':
    migrate()
