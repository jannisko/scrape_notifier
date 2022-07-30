#!/usr/bin/env python
import sqlite3

con = sqlite3.connect('users.db')
cur = con.cursor()

cur.execute("select * from users")
print(cur.fetchall())
