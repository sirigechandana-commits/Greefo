import sqlite3

conn = sqlite3.connect("greefo.db")
cursor = conn.cursor()

cursor.execute(
    "INSERT INTO messages (text, created_at) VALUES (?, ?)",
    (text, created_at)
)

conn.commit()
conn.close()

print("Admin user created successfully")
