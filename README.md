# 🕒 Attendance Management System (Flask + SQLite)

A **local Attendance Management System** built using **Python (Flask)** and **SQLite**, designed for small organizations (around 10 employees).  
The application runs **locally**, supports **role-based access**, and provides attendance tracking, leave management, and Excel report generation.

---

## 🚀 Features

### 🔐 Authentication & Roles
- Secure login system
- Role-based access control
  - **Admin**
  - **Employee**

### 🧑‍💼 Employee Management (Admin)
- Add new employees
- View employee list
- Assign department and role

### ⏱ Attendance Management
- Daily **Check-In / Check-Out**
- Automatic attendance status calculation:
  - Present
  - Late
  - Half Day
- Prevents duplicate check-ins

### 📅 Leave Management
- Employees can apply for leave
- Admin can approve leave requests
- Leave status tracking

### 📊 Reports
- Export attendance data to **Excel (.xlsx)**
- Auto-generated reports stored locally

### 🗄 Database
- SQLite (file-based local database)
- No internet connection required

---

## 🛠 Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS (Jinja2 Templates),
- **Reports:** Pandas, OpenPyXL,numpy
- **Version Control:** Git & GitHub


---

## 📁 Project Structure

attendance_app/
│
├── app.py
├── db.py
├── config.py
├── create_admin.py
├── requirements.txt
├── .gitignore
│
├── templates/
│ ├── login.html
│ ├── dashboard.html
│ ├── attendance.html
│ ├── admin.html
│
├── static/
│ └── style.css
│
├── reports/
│ └── attendance_report.xlsx