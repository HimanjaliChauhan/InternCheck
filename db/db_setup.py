import sqlite3
from pathlib import Path

# Path to database file inside db/ folder
DB_PATH = Path(__file__).resolve().parent / "companies.db"

# Connect (creates db file if it doesn’t exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ------------------ USERS TABLE ------------------
# Stores faculty login accounts
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# ------------------ WHITELIST TABLE ------------------
# Stores trusted companies
cursor.execute("""
CREATE TABLE IF NOT EXISTS whitelist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT UNIQUE NOT NULL
)
""")

# ------------------ BLACKLIST TABLE ------------------
# Stores scam/blocked companies
cursor.execute("""
CREATE TABLE IF NOT EXISTS blacklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT UNIQUE NOT NULL
)
""")

# ------------------ REPORTS TABLE ------------------
# Stores student reports about postings
cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    posting_id TEXT NOT NULL,
    user_feedback TEXT NOT NULL,
    reason TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database setup complete. companies.db is ready inside db/")

