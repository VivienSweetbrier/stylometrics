import sqlite3
import pandas as pd
conn = sqlite3.connect('data/processed/hebrew.db')
print(pd.read_sql_query('SELECT * FROM words LIMIT 5', conn))

