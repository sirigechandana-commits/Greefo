import sqlite3

conn = sqlite3.connect("greefo.db")
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# MESSAGES TABLE (if not already there)
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    created_at TEXT
)
""")

conn.commit()
conn.close()

print("Database tables created successfully")
