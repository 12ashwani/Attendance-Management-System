from flask import Flask, render_template, request, redirect, session
from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash

from datetime import datetime
from config import LATE_TIME, HALF_DAY_TIME
import pandas as pd

app = Flask(__name__)
app.secret_key = "attendance_secret"



# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT password, role, emp_id FROM users WHERE username=?",
            (username,)
        )
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["role"] = user[1]
            session["emp_id"] = user[2]
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")



# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect("/")
    return render_template("dashboard.html", role=session["role"])


# ---------------- ATTENDANCE LOGIC ----------------
def get_status(check_in):
    if check_in <= LATE_TIME:
        return "Present"
    elif check_in <= HALF_DAY_TIME:
        return "Late"
    else:
        return "Half Day"


@app.route("/checkin")
def checkin():
    if "emp_id" not in session:
        return redirect("/")

    emp_id = session["emp_id"]
    date = datetime.today().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M")

    status = get_status(time)

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM attendance WHERE emp_id=? AND date=?",
        (emp_id, date)
    )
    if cur.fetchone():
        conn.close()
        return "Already checked in"

    cur.execute("""
        INSERT INTO attendance (emp_id, date, check_in, status)
        VALUES (?, ?, ?, ?)
    """, (emp_id, date, time, status))

    conn.commit()
    conn.close()
    return "Check-In Successful"


@app.route("/checkout")
def checkout():
    if "emp_id" not in session:
        return redirect("/")

    emp_id = session["emp_id"]
    date = datetime.today().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE attendance
        SET check_out=?
        WHERE emp_id=? AND date=?
    """, (time, emp_id, date))

    conn.commit()
    conn.close()
    return "Check-Out Successful"


# ---------------- LEAVE MANAGEMENT ----------------
@app.route("/apply_leave", methods=["POST"])
def apply_leave():
    if "emp_id" not in session:
        return redirect("/")

    emp_id = session["emp_id"]
    from_date = request.form["from"]
    to_date = request.form["to"]
    leave_type = request.form["type"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO leave_requests
        (emp_id, from_date, to_date, leave_type, status)
        VALUES (?, ?, ?, ?, 'Pending')
    """, (emp_id, from_date, to_date, leave_type))

    conn.commit()
    conn.close()
    return "Leave Applied"


@app.route("/approve_leave/<int:id>")
def approve_leave(id):
    if session.get("role") not in ["Admin", "HR"]:
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE leave_requests SET status='Approved' WHERE id=?",
        (id,)
    )
    conn.commit()
    conn.close()
    return "Leave Approved"


# ---------------- EXCEL REPORT ----------------
@app.route("/export")
def export_excel():
    if session.get("role") not in ["Admin", "HR"]:
        return "Unauthorized"

    conn = get_db()
    df = pd.read_sql("SELECT * FROM attendance", conn)
    conn.close()

    file_path = "reports/attendance_report.xlsx"
    df.to_excel(file_path, index=False)

    return "Excel Report Generated"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin_panel():
    if session.get("role") not in ["Admin", "HR"]:
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, emp_code, name, department FROM employees")
    employees = cur.fetchall()
    conn.close()

    return render_template("admin.html", employees=employees)

# ---------------- ADD EMPLOYEE ----------------

@app.route("/add_employee", methods=["POST"])
def add_employee():
    if session.get("role") not in ["Admin", "HR"]:
        return "Unauthorized"

    emp_code = request.form["emp_code"]
    name = request.form["name"]
    department = request.form["department"]
    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]

    conn = get_db()
    cur = conn.cursor()

    # Insert employee
    cur.execute(
        "INSERT INTO employees (emp_code, name, department) VALUES (?, ?, ?)",
        (emp_code, name, department)
    )
    emp_id = cur.lastrowid

    # ✅ HASH PASSWORD HERE
    hashed_password = generate_password_hash(password)

    # Insert login user
    cur.execute("""
        INSERT INTO users (emp_id, username, password, role)
        VALUES (?, ?, ?, ?)
    """, (emp_id, username, hashed_password, role))

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------------- ATTENDANCE VIEW ----------------
@app.route("/attendance")
def view_attendance():
    if "role" not in session:
        return redirect("/")

    role = session["role"]
    emp_id = session.get("emp_id")

    date = request.args.get("date")
    month = request.args.get("month")

    conn = get_db()
    cur = conn.cursor()

    base_query = """
        SELECT e.emp_code, e.name, a.date, a.check_in, a.check_out, a.status
        FROM attendance a
        JOIN employees e ON a.emp_id = e.id
    """

    conditions = []
    params = []

    if role == "Employee":
        conditions.append("a.emp_id = ?")
        params.append(emp_id)

    if date:
        conditions.append("a.date = ?")
        params.append(date)

    if month:
        conditions.append("strftime('%Y-%m', a.date) = ?")
        params.append(month)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY a.date DESC"

    cur.execute(base_query, params)
    records = cur.fetchall()
    conn.close()

    return render_template("attendance.html", records=records)
# ---------------- LEAVE PAGES ----------------
@app.route("/leave")
def leave_page():
    if "emp_id" not in session:
        return redirect("/")

    emp_id = session["emp_id"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT from_date, to_date, leave_type, status
        FROM leave_requests
        WHERE emp_id=?
        ORDER BY id DESC
    """, (emp_id,))
    leaves = cur.fetchall()
    conn.close()

    return render_template("leave.html", leaves=leaves)


@app.route("/leave_approval")

def leave_approval():
    if session.get("role") not in ["Admin", "HR"]:
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT lr.id, e.emp_code, e.name,
               lr.from_date, lr.to_date, lr.leave_type, lr.status
        FROM leave_requests lr
        JOIN employees e ON lr.emp_id = e.id
        ORDER BY lr.id DESC
    """)
    leaves = cur.fetchall()
    conn.close()

    return render_template("leave_approval.html", leaves=leaves)
# ---------------- DELETE EMPLOYEE ----------------

@app.route("/delete_employee/<int:emp_id>")
def delete_employee(emp_id):
    if session.get("role") not in ["Admin", "HR"]:
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    # Delete dependent records first
    cur.execute("DELETE FROM users WHERE emp_id=?", (emp_id,))
    cur.execute("DELETE FROM attendance WHERE emp_id=?", (emp_id,))
    cur.execute("DELETE FROM leave_requests WHERE emp_id=?", (emp_id,))

    # Finally delete employee
    cur.execute("DELETE FROM employees WHERE id=?", (emp_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")
@app.route("/mark_absent", methods=["POST"])
def mark_absent():
    if session.get("role") not in ["Admin", "HR"]:
        return "Unauthorized"

    emp_id = request.form["emp_id"]
    date = request.form["date"]

    conn = get_db()
    cur = conn.cursor()

    # Check if attendance already exists
    cur.execute(
        "SELECT id FROM attendance WHERE emp_id=? AND date=?",
        (emp_id, date)
    )
    if cur.fetchone():
        conn.close()
        return "Attendance already exists for this date"

    # Insert Absent record
    cur.execute("""
        INSERT INTO attendance (emp_id, date, status)
        VALUES (?, ?, 'Absent')
    """, (emp_id, date))

    conn.commit()
    conn.close()

    return redirect("/admin")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
