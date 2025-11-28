import sqlite3

# Connect to database
conn = sqlite3.connect("db/companies.db")
cursor = conn.cursor()

# Ensure users table exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Insert a default admin user
try:
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "password123"))
    print("✅ Admin user created: username=admin, password=password123")
except sqlite3.IntegrityError:
    print("⚠️ Admin user already exists")

conn.commit()
conn.close()
