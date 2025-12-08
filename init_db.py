import sqlite3
from pathlib import Path
p = Path(__file__).parent / 'library.db'
sql = Path(__file__).parent / 'db_init.sql'
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.executescript(sql.read_text())
conn.commit()
conn.close()
print('Initialized DB at', p)
