import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# POSTS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
)
""")

# REPLIES TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    reply TEXT NOT NULL,
    created_at TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ Database and tables created successfully")
