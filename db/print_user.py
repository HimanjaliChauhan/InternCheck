# db/print_users.py
import sqlite3
from pathlib import Path
DB_PATH = Path(__file__).resolve().parent / "companies.db"
print("Using DB path:", DB_PATH)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", [t[0] for t in cur.fetchall()])
print("\nUsers table rows:")
try:
    cur.execute("SELECT id, username, password FROM users")
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print("Could not read users table:", e)
conn.close()
