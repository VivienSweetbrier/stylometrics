import sqlite3

conn = sqlite3.connect('data/processed/piraha.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in piraha.db:", tables)
conn.close()
