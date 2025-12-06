import os
import sqlite3
import smtplib
from datetime import date, timedelta
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv

load_dotenv() 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_your_project_that_is_long_and_random'
DATABASE = 'attendance.db'

# --- Database Helper Functions ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Decorators for Access Control ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("role") != required_role:
                flash(f"You do not have permission for this action.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# --- Email Sending Function ---
'''def send_attendance_alert(student_email, student_name, course_name, percentage):
    if not os.getenv('EMAIL_USER') or not os.getenv('EMAIL_PASS'):
        print("Email credentials not configured. Skipping email.")
        return
    subject = "Low Attendance Warning"
    body = f"""Dear {student_name},\n\nThis is a reminder that your attendance for the course '{course_name}' is currently {percentage:.2f}%.\nThis is below the required 75% threshold. Please go and meet you respective mentor or professor.\n\nRegards,\nSmart Attendance Tracker System"""
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = student_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
            smtp_server.sendmail(os.getenv('EMAIL_USER'), student_email, msg.as_string())
        print(f"Alert sent to {student_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")'''

# --- NEW VERSION (without .env) ---
def send_attendance_alert(student_email, student_name, course_name, percentage):
    # --- Hardcoded Credentials ---
    SENDER_EMAIL = "iconicno18@gmail.com"  # <-- PUT YOUR GMAIL HERE
    SENDER_APP_PASSWORD = "oihoegwdygbuzckb" # <-- PUT YOUR 16-DIGIT APP PASSWORD HERE

    subject = "Low Attendance Warning"
    body = f"""Dear {student_name},\n\nThis is a reminder that your attendance for the course '{course_name}' is currently {percentage:.2f}%.\nThis is below the required 75% threshold. Please go and meet you respective mentor or professor.\n\nRegards,\nSmart Attendance Tracker System"""
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = student_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            smtp_server.sendmail(SENDER_EMAIL, student_email, msg.as_string())
        print(f"Alert sent to {student_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- LOGIN LOGIC HELPER ---
def handle_login(role_to_check):
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE (username = ? OR email = ?) AND role = ?", 
                          (username, username, role_to_check)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash('Logged in successfully!', 'success')
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials or role mismatch.", "danger")
    return None

# --- PUBLIC ROUTES ---
@app.route("/login", methods=["GET", "POST"])
def login(): # Admin Login
    response = handle_login('admin')
    if response: return response
    return render_template("login.html")

@app.route("/student_login", methods=["GET", "POST"])
def student_login():
    response = handle_login('student')
    if response: return response
    return render_template("student_login.html")

@app.route("/faculty_login", methods=["GET", "POST"])
def faculty_login():
    response = handle_login('faculty')
    if response: return response
    return render_template("faculty_login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if "user_id" in session: return redirect(url_for("index"))
    if request.method == 'POST':
        full_name, email, username = request.form['full_name'], request.form['email'], request.form['username']
        password = generate_password_hash(request.form['password'])
        db = get_db()
        try:
            result = db.execute("SELECT MAX(student_id) FROM users").fetchone()
            next_id = (result[0] or 0) + 1
            db.execute('INSERT INTO users (student_id, username, password, email, full_name, role) VALUES (?, ?, ?, ?, ?, ?)',
                       (next_id, username, password, email, full_name, 'student'))
            db.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return render_template('register.html')

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# --- CORE REDIRECTION & DASHBOARDS ---
@app.route("/")
@login_required
def index():
    role = session.get("role")
    if role == "admin": return redirect(url_for("admin_dashboard"))
    if role == "faculty": return redirect(url_for("faculty_dashboard"))
    if role == "student": return redirect(url_for("student_dashboard"))
    return redirect(url_for("logout"))

@app.route("/admin/dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/faculty/dashboard")
@login_required
@role_required("faculty")
def faculty_dashboard():
    return render_template("faculty_dashboard.html")

@app.route("/student/dashboard")
@login_required
@role_required("student")
def student_dashboard():
    db = get_db()
    student_user_id = session['user_id']
    query = "SELECT c.name as course_name, (SELECT COUNT(*) FROM attendance WHERE course_id = c.id) as total_classes, (SELECT COUNT(*) FROM attendance WHERE student_user_id = ? AND course_id = c.id AND status = 'Present') as present_classes FROM courses c"
    courses_attendance = db.execute(query, (student_user_id,)).fetchall()
    summary = []
    for course in courses_attendance:
        if course['total_classes'] > 0:
            percentage = (course['present_classes'] / course['total_classes']) * 100
            summary.append({ 'course_name': course['course_name'], 'percentage': percentage, 'is_low': percentage < 75 })
    return render_template("student_dashboard.html", summary=summary)

# --- ATTENDANCE ROUTES ---
@app.route('/attendance/take', methods=['GET', 'POST'])
@login_required
def take_attendance():
    if session['role'] not in ['admin', 'faculty']:
        flash('Permission denied.', 'danger'); return redirect(url_for('index'))
    db = get_db()
    
    if request.method == 'POST':
        course_id = request.form['course_id']
        attendance_date = request.form['date']
        
        # Get the list of ALL students who were on the form
        all_student_ids = request.form.getlist('all_students')
        # Get the list of ONLY the students who were marked present
        present_student_ids = request.form.getlist('present_students')

        # Loop through every student that was displayed
        for student_id in all_student_ids:
            # Check if this student's ID is in the list of 'present' students
            if student_id in present_student_ids:
                status = 'Present'
            else:
                status = 'Absent'
            
            # Save the record for this student
            db.execute("INSERT OR REPLACE INTO attendance (student_user_id, course_id, date, status) VALUES (?, ?, ?, ?)",
                       (student_id, course_id, attendance_date, status))
        
        db.commit()
        flash('Attendance recorded successfully!', 'success')
        check_and_send_alerts(course_id)
        
        # Redirect back to the take_attendance page to select another course
        return redirect(url_for('take_attendance'))
    
    # --- The GET request logic remains the same ---
    courses = []
    if session['role'] == 'admin': 
        courses = db.execute("SELECT id, name FROM courses ORDER BY name").fetchall()
    else: 
        courses = db.execute("SELECT id, name FROM courses WHERE faculty_id = ? ORDER BY name", (session['user_id'],)).fetchall()
    
    selected_course_id = request.args.get('view_course_id', type=int)
    students = []
    if selected_course_id:
        students = db.execute("SELECT id, full_name FROM users WHERE role = 'student' ORDER BY full_name").fetchall()
    
    start_date, end_date = date.today(), date.today() + timedelta(days=10)
    
    return render_template('take_attendance.html', 
                           courses=courses, 
                           students=students, 
                           selected_course_id=selected_course_id, 
                           start_date=start_date, 
                           end_date=end_date)

@app.route('/attendance/modify', methods=['GET', 'POST'])
@login_required
def modify_attendance():
    if session['role'] not in ['admin', 'faculty']:
        flash('Permission denied.', 'danger'); return redirect(url_for('index'))
    db = get_db()
    if request.method == 'POST':
        course_id, date = request.form.get('course_id'), request.form.get('date')
        student_ids, statuses = request.form.getlist('student_id'), request.form.getlist('status')
        for i in range(len(student_ids)):
            db.execute("UPDATE attendance SET status = ? WHERE student_user_id = ? AND course_id = ? AND date = ?", (statuses[i], student_ids[i], course_id, date))
        db.commit()
        flash('Attendance updated successfully!', 'success')
        check_and_send_alerts(course_id)
        return redirect(url_for('modify_attendance', course_id=course_id, date=date))
    
    courses = []
    if session['role'] == 'admin': courses = db.execute("SELECT id, name FROM courses ORDER BY name").fetchall()
    else: courses = db.execute("SELECT id, name FROM courses WHERE faculty_id = ? ORDER BY name", (session['user_id'],)).fetchall()
    
    selected_course_id, selected_date = request.args.get('course_id', type=int), request.args.get('date')
    attendance_records = None
    if selected_course_id and selected_date:
        query = "SELECT u.full_name, a.status, a.student_user_id FROM attendance a JOIN users u ON a.student_user_id = u.id WHERE a.course_id = ? AND a.date = ? ORDER BY u.full_name"
        attendance_records = db.execute(query, (selected_course_id, selected_date)).fetchall()
    return render_template('modify_attendance.html', courses=courses, selected_course_id=selected_course_id, selected_date=selected_date, attendance_records=attendance_records)

# --- ADMIN MANAGEMENT & OTHER ROUTES ---
@app.route('/admin/manage_users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_users():
    db = get_db()
    if request.method == 'POST':
        username, email, full_name, role = request.form['username'], request.form['email'], request.form['full_name'], request.form['role']
        password = generate_password_hash(request.form['password'])
        student_id, faculty_id = None, None
        try:
            if role == 'student':
                result = db.execute("SELECT MAX(student_id) FROM users").fetchone(); student_id = (result[0] or 0) + 1
            elif role == 'faculty':
                result = db.execute("SELECT MAX(faculty_id) FROM users").fetchone(); faculty_id = (result[0] or 0) + 1
            db.execute('INSERT INTO users (student_id, faculty_id, username, password, email, full_name, role) VALUES (?, ?, ?, ?, ?, ?, ?)',(student_id, faculty_id, username, password, email, full_name, role))
            db.commit()
            flash(f'{role.capitalize()} "{full_name}" added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        return redirect(url_for('manage_users'))
    students = db.execute("SELECT * FROM users WHERE role = 'student' ORDER BY student_id").fetchall()
    faculties = db.execute("SELECT * FROM users WHERE role = 'faculty' ORDER BY faculty_id").fetchall()
    return render_template('manage_users.html', students=students, faculties=faculties)

@app.route('/admin/manage_courses', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_courses():
    db = get_db()
    if request.method == 'POST':
        name, faculty_id = request.form['name'], request.form['faculty_id']
        try:
            db.execute('INSERT INTO courses (name, faculty_id) VALUES (?, ?)', (name, faculty_id))
            db.commit()
            flash('Course added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Course name already exists.', 'danger')
        return redirect(url_for('manage_courses'))
    courses = db.execute("SELECT c.id, c.name, u.full_name as faculty_name FROM courses c LEFT JOIN users u ON c.faculty_id = u.id").fetchall()
    faculties = db.execute("SELECT id, full_name FROM users WHERE role = 'faculty'").fetchall()
    return render_template('manage_courses.html', courses=courses, faculties=faculties)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password, new_password, confirm_password = request.form['current_password'], request.form['new_password'], request.form['confirm_password']
        user_id = session['user_id']
        db = get_db()
        user = db.execute('SELECT password FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user or not check_password_hash(user['password'], current_password):
            flash('Your current password is not correct.', 'danger'); return redirect(url_for('change_password'))
        if new_password != confirm_password:
            flash('New password and confirmation do not match.', 'danger'); return redirect(url_for('change_password'))
        db.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(new_password), user_id))
        db.commit()
        flash('Your password has been updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('change_password.html')

'''def check_and_send_alerts(course_id):
    db = get_db()
    course = db.execute("SELECT name FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course: return
    all_students = db.execute("SELECT id, email, full_name FROM users WHERE role = 'student'").fetchall()
    for student in all_students:
        stats_query = "SELECT COUNT(*) as total, SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present FROM attendance WHERE student_user_id = ? AND course_id = ?"
        stats = db.execute(stats_query, (student['id'], course_id)).fetchone()
        total, present = (stats['total'] or 0), (stats['present'] or 0)
        if total > 0:
            percentage = (present / total) * 100
            if percentage < 75:
                send_attendance_alert(student['email'], student['full_name'], course['name'], percentage)'''

# --- NEW VERSION (calculates for a specific 15-day period) ---
def check_and_send_alerts(course_id):
    db = get_db()
    course = db.execute("SELECT name FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course: return
    
    # --- Define the 15-day period ---
    PERIOD_START_DATE = "2025-07-25"
    PERIOD_END_DATE = "2025-08-08" # This is 15 days including the start date

    all_students = db.execute("SELECT id, email, full_name FROM users WHERE role = 'student'").fetchall()
    for student in all_students:
        # The query now includes a date filter
        stats_query = f"""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present
            FROM attendance 
            WHERE student_user_id = ? 
              AND course_id = ?
              AND date BETWEEN '{PERIOD_START_DATE}' AND '{PERIOD_END_DATE}'
        """
        stats = db.execute(stats_query, (student['id'], course_id)).fetchone()
        
        total, present = (stats['total'] or 0), (stats['present'] or 0)
        if total > 0:
            percentage = (present / total) * 100
            if percentage < 75:
                send_attendance_alert(student['email'], student['full_name'], course['name'], percentage)

if __name__ == '__main__':
    app.run(debug=True)