import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Ensure users table exists
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    profile_pic TEXT DEFAULT 'default.png'
)
""")

# Check if admin exists
cur.execute("SELECT username FROM users WHERE username='admin'")
row = cur.fetchone()

if row:
    print("Admin user already exists!")
else:
    cur.execute(
        "INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
        ("admin", "admin123", "default.png")
    )
    conn.commit()
    print("Admin user created! Username: admin, Password: admin123")

conn.close()
