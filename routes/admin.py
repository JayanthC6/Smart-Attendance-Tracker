from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Course, Attendance
from services import AttendanceService, ReportService, NotificationService
from datetime import date, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get system statistics
    total_students = User.query.filter_by(role='student', is_active=True).count()
    total_faculty = User.query.filter_by(role='faculty', is_active=True).count()
    total_courses = Course.query.filter_by(is_active=True).count()
    
    # Get recent attendance data
    recent_attendance = db.session.query(Attendance).order_by(
        Attendance.created_at.desc()
    ).limit(10).all()
    
    # Get low attendance students
    low_attendance_students = []
    students = User.query.filter_by(role='student', is_active=True).all()
    
    for student in students:
        for course in Course.query.filter_by(is_active=True).all():
            percentage = student.get_attendance_percentage(course.id)
            if 0 < percentage < 75:  # Low attendance but has some records
                low_attendance_students.append({
                    'student': student,
                    'course': course,
                    'percentage': percentage
                })
    
    # Limit to top 10
    low_attendance_students = sorted(low_attendance_students, 
                                   key=lambda x: x['percentage'])[:10]
    
    stats = {
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_courses': total_courses,
        'recent_attendance': recent_attendance,
        'low_attendance_students': low_attendance_students
    }
    
    return render_template("admin/dashboard.html", stats=stats)

@admin_bp.route('/manage_users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    """Manage users (students and faculty)"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        full_name = request.form['full_name']
        role = request.form['role']
        password = request.form['password']
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        try:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                is_active=True
            )
            
            # Set role-specific ID
            if role == 'student':
                result = db.session.query(db.func.max(User.student_id)).scalar()
                user.student_id = (result or 0) + 1
            elif role == 'faculty':
                result = db.session.query(db.func.max(User.faculty_id)).scalar()
                user.faculty_id = (result or 0) + 1
            
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Create notification
            NotificationService.create_notification(
                user.id,
                "Account Created",
                f"Your {role} account has been created successfully.",
                "info"
            )
            
            flash(f'{role.capitalize()} "{full_name}" added successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the user.', 'danger')
        
        return redirect(url_for('admin.manage_users'))
    
    # Get users
    students = User.query.filter_by(role='student', is_active=True).order_by(User.student_id).all()
    faculties = User.query.filter_by(role='faculty', is_active=True).order_by(User.faculty_id).all()
    
    return render_template('admin/manage_users.html', students=students, faculties=faculties)

@admin_bp.route('/manage_courses', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_courses():
    """Manage courses"""
    if request.method == 'POST':
        name = request.form['name']
        code = request.form.get('code', '')
        faculty_id = request.form.get('faculty_id') or None
        description = request.form.get('description', '')
        credits = int(request.form.get('credits', 3))
        
        # Check if course already exists
        existing_course = Course.query.filter(
            (Course.name == name) | (Course.code == code)
        ).first()
        
        if existing_course:
            flash('Course name or code already exists.', 'danger')
            return redirect(url_for('admin.manage_courses'))
        
        try:
            course = Course(
                name=name,
                code=code,
                faculty_id=faculty_id,
                description=description,
                credits=credits,
                is_active=True
            )
            
            db.session.add(course)
            db.session.commit()
            
            flash('Course added successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the course.', 'danger')
        
        return redirect(url_for('admin.manage_courses'))
    
    # Get courses and faculties
    courses = db.session.query(Course, User.full_name).outerjoin(
        User, Course.faculty_id == User.id
    ).filter(Course.is_active == True).all()
    
    faculties = User.query.filter_by(role='faculty', is_active=True).all()
    
    return render_template('admin/manage_courses.html', courses=courses, faculties=faculties)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate reports"""
    # Get date range from request
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    
    # Convert to date objects
    try:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)
    except ValueError:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
    
    # Get attendance summary
    attendance_summary = ReportService.get_attendance_summary(
        start_date=start_date, 
        end_date=end_date
    )
    
    # Get course-wise statistics
    courses = Course.query.filter_by(is_active=True).all()
    course_stats = []
    
    for course in courses:
        summary = course.get_attendance_summary(start_date, end_date)
        course_stats.append({
            'course': course,
            'summary': summary
        })
    
    return render_template('admin/reports.html', 
                         attendance_summary=attendance_summary,
                         course_stats=course_stats,
                         start_date=start_date,
                         end_date=end_date)

@admin_bp.route('/system_settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    """System settings"""
    if request.method == 'POST':
        # Handle settings update
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.system_settings'))
    
    return render_template('admin/system_settings.html')
