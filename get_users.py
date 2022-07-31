#!/usr/bin/env python
import sqlite3

con = sqlite3.connect("data/db.sqlite")
cur = con.cursor()

cur.execute("select * from users")
print(cur.fetchall())
