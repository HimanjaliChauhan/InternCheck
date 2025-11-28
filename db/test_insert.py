# db/test_insert.py
import sqlite3
from pathlib import Path
DB_PATH = Path(__file__).resolve().parent / "companies.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("INSERT INTO reports (posting_id, user_feedback, reason) VALUES (?,?,?)",
            ("test-posting-123","fake","test insert"))
conn.commit()
print("Inserted test report.")
cur.execute("SELECT id,posting_id,user_feedback,reason FROM reports ORDER BY id DESC LIMIT 1")
print("Last report:", cur.fetchone())
conn.close()
