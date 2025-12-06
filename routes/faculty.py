from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Course, Attendance
from services import AttendanceService, ReportService
from datetime import date, timedelta

faculty_bp = Blueprint('faculty', __name__)

def faculty_required(f):
    """Decorator to require faculty role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'faculty':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@faculty_bp.route("/dashboard")
@login_required
@faculty_required
def dashboard():
    """Faculty dashboard"""
    # Get faculty's courses
    courses = Course.query.filter_by(faculty_id=current_user.id, is_active=True).all()
    
    # Get course statistics
    course_stats = []
    for course in courses:
        summary = course.get_attendance_summary()
        course_stats.append({
            'course': course,
            'summary': summary
        })
    
    # Get recent attendance records
    recent_attendance = db.session.query(Attendance, Course.name).join(
        Course, Attendance.course_id == Course.id
    ).filter(
        Course.faculty_id == current_user.id
    ).order_by(Attendance.created_at.desc()).limit(10).all()
    
    # Get low attendance students for faculty's courses
    low_attendance_students = []
    for course in courses:
        students = User.query.filter_by(role='student', is_active=True).all()
        for student in students:
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
        'courses': courses,
        'course_stats': course_stats,
        'recent_attendance': recent_attendance,
        'low_attendance_students': low_attendance_students
    }
    
    return render_template("faculty/dashboard.html", stats=stats)

@faculty_bp.route('/take_attendance', methods=['GET', 'POST'])
@login_required
@faculty_required
def take_attendance():
    """Take attendance for a course"""
    if request.method == 'POST':
        course_id = request.form['course_id']
        attendance_date = request.form['date']
        
        # Get the list of ALL students who were on the form
        all_student_ids = request.form.getlist('all_students')
        # Get the list of ONLY the students who were marked present
        present_student_ids = request.form.getlist('present_students')
        
        try:
            # Loop through every student that was displayed
            for student_id in all_student_ids:
                # Check if this student's ID is in the list of 'present' students
                if student_id in present_student_ids:
                    status = 'Present'
                else:
                    status = 'Absent'
                
                # Save the record for this student
                attendance = Attendance(
                    student_user_id=int(student_id),
                    course_id=int(course_id),
                    date=date.fromisoformat(attendance_date),
                    status=status
                )
                db.session.add(attendance)
            
            db.session.commit()
            flash('Attendance recorded successfully!', 'success')
            
            # Check and send alerts
            AttendanceService.check_and_send_alerts(int(course_id))
            
            # Redirect back to the take_attendance page to select another course
            return redirect(url_for('faculty.take_attendance'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while recording attendance.', 'danger')
    
    # Get faculty's courses
    courses = Course.query.filter_by(faculty_id=current_user.id, is_active=True).order_by(Course.name).all()
    
    selected_course_id = request.args.get('view_course_id', type=int)
    students = []
    if selected_course_id:
        # Verify the course belongs to this faculty
        course = Course.query.filter_by(id=selected_course_id, faculty_id=current_user.id).first()
        if course:
            students = User.query.filter_by(role='student', is_active=True).order_by(User.full_name).all()
    
    start_date = date.today()
    end_date = date.today() + timedelta(days=10)
    
    return render_template('faculty/take_attendance.html', 
                         courses=courses, 
                         students=students, 
                         selected_course_id=selected_course_id, 
                         start_date=start_date, 
                         end_date=end_date)

@faculty_bp.route('/modify_attendance', methods=['GET', 'POST'])
@login_required
@faculty_required
def modify_attendance():
    """Modify attendance records"""
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        attendance_date = request.form.get('date')
        student_ids = request.form.getlist('student_id')
        statuses = request.form.getlist('status')
        
        try:
            for i in range(len(student_ids)):
                attendance = Attendance.query.filter_by(
                    student_user_id=int(student_ids[i]),
                    course_id=int(course_id),
                    date=date.fromisoformat(attendance_date)
                ).first()
                
                if attendance:
                    attendance.status = statuses[i]
            
            db.session.commit()
            flash('Attendance updated successfully!', 'success')
            
            # Check and send alerts
            AttendanceService.check_and_send_alerts(int(course_id))
            
            return redirect(url_for('faculty.modify_attendance', 
                                  course_id=course_id, 
                                  date=attendance_date))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating attendance.', 'danger')
    
    # Get faculty's courses
    courses = Course.query.filter_by(faculty_id=current_user.id, is_active=True).order_by(Course.name).all()
    
    selected_course_id = request.args.get('course_id', type=int)
    selected_date = request.args.get('date')
    attendance_records = None
    
    if selected_course_id and selected_date:
        # Verify the course belongs to this faculty
        course = Course.query.filter_by(id=selected_course_id, faculty_id=current_user.id).first()
        if course:
            attendance_records = db.session.query(Attendance, User.full_name).join(
                User, Attendance.student_user_id == User.id
            ).filter(
                Attendance.course_id == selected_course_id,
                Attendance.date == date.fromisoformat(selected_date)
            ).order_by(User.full_name).all()
    
    return render_template('faculty/modify_attendance.html', 
                         courses=courses, 
                         selected_course_id=selected_course_id, 
                         selected_date=selected_date, 
                         attendance_records=attendance_records)

@faculty_bp.route('/my_courses')
@login_required
@faculty_required
def my_courses():
    """View faculty's courses"""
    courses = Course.query.filter_by(faculty_id=current_user.id, is_active=True).all()
    
    course_details = []
    for course in courses:
        summary = course.get_attendance_summary()
        course_details.append({
            'course': course,
            'summary': summary
        })
    
    return render_template('faculty/my_courses.html', course_details=course_details)

@faculty_bp.route('/course/<int:course_id>')
@login_required
@faculty_required
def course_details(course_id):
    """View detailed course information"""
    course = Course.query.filter_by(id=course_id, faculty_id=current_user.id, is_active=True).first()
    
    if not course:
        flash('Course not found or you do not have access to it.', 'danger')
        return redirect(url_for('faculty.my_courses'))
    
    # Get students enrolled in this course (all students for now)
    students = User.query.filter_by(role='student', is_active=True).order_by(User.full_name).all()
    
    # Get attendance data for each student
    student_attendance = []
    for student in students:
        percentage = student.get_attendance_percentage(course_id)
        student_attendance.append({
            'student': student,
            'percentage': percentage,
            'is_low': percentage < 75
        })
    
    # Get attendance summary
    summary = course.get_attendance_summary()
    
    return render_template('faculty/course_details.html', 
                         course=course,
                         student_attendance=student_attendance,
                         summary=summary)
