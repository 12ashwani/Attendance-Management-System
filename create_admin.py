from db import get_db
from werkzeug.security import generate_password_hash

conn = get_db()
cur = conn.cursor()

# 1️⃣ Create Admin employee
cur.execute("""
    INSERT INTO employees (emp_code, name, department)
    VALUES (?, ?, ?)
""", ("ADMIN001", "Admin User", "Administration"))

emp_id = cur.lastrowid   # ✅ NOW emp_id exists

# 2️⃣ Create Admin login with HASHED password
hashed_password = generate_password_hash("admin123")

cur.execute("""
    INSERT INTO users (emp_id, username, password, role)
    VALUES (?, ?, ?, ?)
""", (emp_id, "admin", hashed_password, "Admin"))

conn.commit()
conn.close()

print("✅ Admin user created successfully")
