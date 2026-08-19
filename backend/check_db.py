import sqlite3
db = r'c:\Users\reddy\OneDrive\Desktop\sih-transport\backend\dev_logistics.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)

for t in ['vehicles', 'drivers', 'routes', 'shipments', 'users']:
    if t in tables:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'{t}: {cur.fetchone()[0]} rows')

# Show vehicle statuses
if 'vehicles' in tables:
    cur.execute("SELECT status, COUNT(*) FROM vehicles GROUP BY status")
    rows = cur.fetchall()
    print('Vehicle statuses:', rows)

conn.close()
