import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Users Table with role-specific IDs
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER UNIQUE,
    faculty_id INTEGER UNIQUE,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'faculty', 'student'))
)''')

# Courses Table with the correct foreign key
cursor.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    faculty_id INTEGER,
    FOREIGN KEY (faculty_id) REFERENCES users (id)
)''')

# Attendance Table with the correct foreign key
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
    UNIQUE(student_user_id, course_id, date),
    FOREIGN KEY (student_user_id) REFERENCES users (id),
    FOREIGN KEY (course_id) REFERENCES courses (id)
)''')

# Insert Initial Admin Data
hashed_admin_pass = generate_password_hash('admin123')
cursor.execute("SELECT id FROM users WHERE username = 'admin'")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO users (username, password, email, full_name, role) VALUES (?, ?, ?, ?, ?)",
                   ('admin', hashed_admin_pass, 'admin@example.com', 'Admin User', 'admin'))
    print("Admin user created.")

conn.commit()
conn.close()
print("Database initialized successfully.")