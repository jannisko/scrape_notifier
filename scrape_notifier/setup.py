import sqlite3

db = sqlite3.connect("users.db")
cur = db.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER
    )
"""
)

db.commit()
db.close()
