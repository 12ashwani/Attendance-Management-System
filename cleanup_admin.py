from db import get_db

conn = get_db()
cur = conn.cursor()

cur.execute("DELETE FROM users WHERE username='admin'")
cur.execute("DELETE FROM employees WHERE emp_code='ADMIN001'")

conn.commit()
conn.close()

print("✅ Old admin records deleted")
