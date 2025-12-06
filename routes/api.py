from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Course, Attendance
from services import ReportService, AttendanceService
from datetime import date, timedelta
import json

api_bp = Blueprint('api', __name__)

def api_login_required(f):
    """API decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required_api(required_role):
    """API decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != required_role:
                return jsonify({'error': f'{required_role} role required'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@api_bp.route('/attendance/summary')
@api_login_required
def attendance_summary():
    """Get attendance summary for current user"""
    try:
        if current_user.role == 'student':
            courses = Course.query.filter_by(is_active=True).all()
            summary = []
            
            for course in courses:
                percentage = current_user.get_attendance_percentage(course.id)
                if percentage > 0:
                    summary.append({
                        'course_id': course.id,
                        'course_name': course.name,
                        'course_code': course.code,
                        'percentage': round(percentage, 2),
                        'is_low': percentage < 75
                    })
            
            return jsonify({
                'success': True,
                'data': summary
            })
        
        elif current_user.role == 'faculty':
            courses = Course.query.filter_by(faculty_id=current_user.id, is_active=True).all()
            summary = []
            
            for course in courses:
                course_summary = course.get_attendance_summary()
                summary.append({
                    'course_id': course.id,
                    'course_name': course.name,
                    'course_code': course.code,
                    'total_classes': course_summary['total_records'],
                    'attendance_rate': round(course_summary['attendance_rate'], 2)
                })
            
            return jsonify({
                'success': True,
                'data': summary
            })
        
        else:
            return jsonify({'error': 'Invalid role'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/attendance/trend/<int:course_id>')
@api_login_required
def attendance_trend(course_id):
    """Get attendance trend for a course"""
    try:
        days = request.args.get('days', 30, type=int)
        
        if current_user.role == 'student':
            trend_data = ReportService.get_student_attendance_trend(
                current_user.id, course_id, days
            )
        else:
            # For faculty/admin - get overall course trend
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            attendance_records = db.session.query(Attendance).filter(
                Attendance.course_id == course_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).order_by(Attendance.date).all()
            
            trend_data = []
            for record in attendance_records:
                trend_data.append({
                    'date': record.date.isoformat(),
                    'status': record.status,
                    'student_id': record.student_user_id
                })
        
        return jsonify({
            'success': True,
            'data': trend_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/courses')
@api_login_required
def get_courses():
    """Get courses based on user role"""
    try:
        if current_user.role == 'student':
            courses = Course.query.filter_by(is_active=True).all()
        elif current_user.role == 'faculty':
            courses = Course.query.filter_by(faculty_id=current_user.id, is_active=True).all()
        else:  # admin
            courses = Course.query.filter_by(is_active=True).all()
        
        course_data = []
        for course in courses:
            course_data.append({
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'faculty_name': course.faculty.full_name if course.faculty else 'Not Assigned',
                'credits': course.credits
            })
        
        return jsonify({
            'success': True,
            'data': course_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/students')
@api_login_required
@role_required_api('admin')
def get_students():
    """Get all students (admin only)"""
    try:
        students = User.query.filter_by(role='student', is_active=True).all()
        
        student_data = []
        for student in students:
            student_data.append({
                'id': student.id,
                'student_id': student.student_id,
                'username': student.username,
                'full_name': student.full_name,
                'email': student.email
            })
        
        return jsonify({
            'success': True,
            'data': student_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/attendance/bulk', methods=['POST'])
@api_login_required
@role_required_api('faculty')
def bulk_attendance():
    """Bulk attendance entry (faculty only)"""
    try:
        data = request.get_json()
        course_id = data.get('course_id')
        attendance_date = data.get('date')
        attendance_data = data.get('attendance_data', [])
        
        if not all([course_id, attendance_date, attendance_data]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify course belongs to faculty
        course = Course.query.filter_by(
            id=course_id, 
            faculty_id=current_user.id, 
            is_active=True
        ).first()
        
        if not course:
            return jsonify({'error': 'Course not found or access denied'}), 404
        
        # Process attendance data
        success_count = 0
        for record in attendance_data:
            try:
                attendance = Attendance(
                    student_user_id=record['student_id'],
                    course_id=course_id,
                    date=date.fromisoformat(attendance_date),
                    status=record['status']
                )
                db.session.add(attendance)
                success_count += 1
            except Exception as e:
                continue
        
        db.session.commit()
        
        # Check and send alerts
        AttendanceService.check_and_send_alerts(course_id)
        
        return jsonify({
            'success': True,
            'message': f'Attendance recorded for {success_count} students',
            'count': success_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/reports/export')
@api_login_required
@role_required_api('admin')
def export_reports():
    """Export attendance reports (admin only)"""
    try:
        report_type = request.args.get('type', 'summary')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = date.fromisoformat(start_date)
        if end_date:
            end_date = date.fromisoformat(end_date)
        
        if report_type == 'summary':
            summary = ReportService.get_attendance_summary(
                start_date=start_date, 
                end_date=end_date
            )
            return jsonify({
                'success': True,
                'data': summary
            })
        
        return jsonify({'error': 'Invalid report type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/notifications')
@api_login_required
def get_notifications():
    """Get user notifications"""
    try:
        limit = request.args.get('limit', 10, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        query = db.session.query(Notification).filter_by(user_id=current_user.id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'data': notification_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
