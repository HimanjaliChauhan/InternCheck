import sqlite3
from pathlib import Path

# Path to database file
DB_PATH = Path(__file__).resolve().parent / "companies.db"

# Connect to DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📂 Tables in companies.db:")
for t in tables:
    print("-", t[0])

conn.close()
