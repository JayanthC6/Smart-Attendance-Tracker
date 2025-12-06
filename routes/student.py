from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Course, Attendance
from services import ReportService, NotificationService
from datetime import date, timedelta

student_bp = Blueprint('student', __name__)

def student_required(f):
    """Decorator to require student role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    """Student dashboard"""
    # Get all active courses
    courses = Course.query.filter_by(is_active=True).all()
    
    # Calculate attendance for each course
    attendance_summary = []
    for course in courses:
        percentage = current_user.get_attendance_percentage(course.id)
        if percentage > 0:  # Only show courses with attendance data
            attendance_summary.append({
                'course_name': course.name,
                'course_code': course.code,
                'faculty_name': course.faculty.full_name if course.faculty else 'Not Assigned',
                'percentage': percentage,
                'is_low': percentage < 75,
                'total_classes': course.get_total_classes(),
                'present_classes': int((percentage / 100) * course.get_total_classes()) if course.get_total_classes() > 0 else 0
            })
    
    # Sort by percentage (lowest first)
    attendance_summary.sort(key=lambda x: x['percentage'])
    
    # Get recent attendance records
    recent_attendance = db.session.query(Attendance, Course.name).join(
        Course, Attendance.course_id == Course.id
    ).filter(
        Attendance.student_user_id == current_user.id
    ).order_by(Attendance.date.desc()).limit(10).all()
    
    # Get notifications
    notifications = NotificationService.get_user_notifications(current_user.id, limit=5)
    
    stats = {
        'attendance_summary': attendance_summary,
        'recent_attendance': recent_attendance,
        'notifications': notifications,
        'total_courses': len(attendance_summary),
        'low_attendance_courses': len([c for c in attendance_summary if c['is_low']])
    }
    
    return render_template("student/dashboard.html", stats=stats)

@student_bp.route('/my_attendance')
@login_required
@student_required
def my_attendance():
    """View detailed attendance records"""
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
    
    # Get attendance records for the date range
    attendance_records = db.session.query(Attendance, Course.name).join(
        Course, Attendance.course_id == Course.id
    ).filter(
        Attendance.student_user_id == current_user.id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date.desc()).all()
    
    # Get course-wise summary
    courses = Course.query.filter_by(is_active=True).all()
    course_summary = []
    
    for course in courses:
        percentage = current_user.get_attendance_percentage(course.id, start_date, end_date)
        if percentage > 0:  # Only show courses with attendance data
            total_classes = course.get_total_classes(start_date, end_date)
            present_classes = int((percentage / 100) * total_classes) if total_classes > 0 else 0
            
            course_summary.append({
                'course': course,
                'percentage': percentage,
                'total_classes': total_classes,
                'present_classes': present_classes,
                'absent_classes': total_classes - present_classes,
                'is_low': percentage < 75
            })
    
    return render_template('student/my_attendance.html', 
                         attendance_records=attendance_records,
                         course_summary=course_summary,
                         start_date=start_date,
                         end_date=end_date)

@student_bp.route('/attendance_trend/<int:course_id>')
@login_required
@student_required
def attendance_trend(course_id):
    """View attendance trend for a specific course"""
    course = Course.query.filter_by(id=course_id, is_active=True).first()
    
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Get trend data
    trend_data = ReportService.get_student_attendance_trend(
        current_user.id, 
        course_id, 
        days=30
    )
    
    # Calculate current percentage
    current_percentage = current_user.get_attendance_percentage(course_id)
    
    return render_template('student/attendance_trend.html', 
                         course=course,
                         trend_data=trend_data,
                         current_percentage=current_percentage)

@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    """View all notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get paginated notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return render_template('student/notifications.html', notifications=notifications)

@student_bp.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
@student_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    success = NotificationService.mark_notification_read(notification_id, current_user.id)
    
    if success:
        return jsonify({'success': True, 'message': 'Notification marked as read'})
    else:
        return jsonify({'success': False, 'message': 'Failed to mark notification as read'})

@student_bp.route('/mark_all_notifications_read', methods=['POST'])
@login_required
@student_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'All notifications marked as read'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to mark notifications as read'})

@student_bp.route('/course_details/<int:course_id>')
@login_required
@student_required
def course_details(course_id):
    """View detailed course information"""
    course = Course.query.filter_by(id=course_id, is_active=True).first()
    
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Get attendance percentage
    percentage = current_user.get_attendance_percentage(course_id)
    
    # Get attendance records for this course
    attendance_records = Attendance.query.filter_by(
        student_user_id=current_user.id,
        course_id=course_id
    ).order_by(Attendance.date.desc()).all()
    
    # Get trend data
    trend_data = ReportService.get_student_attendance_trend(
        current_user.id, 
        course_id, 
        days=90
    )
    
    return render_template('student/course_details.html', 
                         course=course,
                         percentage=percentage,
                         attendance_records=attendance_records,
                         trend_data=trend_data)
