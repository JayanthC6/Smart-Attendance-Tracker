from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import User, Course, Attendance
from services import ReportService

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """Main landing page"""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard - redirects based on user role"""
    role = current_user.role
    
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif role == "faculty":
        return redirect(url_for("faculty.dashboard"))
    elif role == "student":
        return redirect(url_for("student.dashboard"))
    
    return redirect(url_for("auth.logout"))

@main_bp.route("/profile")
@login_required
def profile():
    """User profile page"""
    # Get user statistics
    stats = {}
    
    if current_user.role == 'student':
        # Get attendance summary for student
        courses = Course.query.filter_by(is_active=True).all()
        attendance_data = []
        
        for course in courses:
            percentage = current_user.get_attendance_percentage(course.id)
            attendance_data.append({
                'course_name': course.name,
                'percentage': percentage,
                'is_low': percentage < 75
            })
        
        stats['attendance_data'] = attendance_data
    
    elif current_user.role == 'faculty':
        # Get course statistics for faculty
        courses = Course.query.filter_by(faculty_id=current_user.id, is_active=True).all()
        course_stats = []
        
        for course in courses:
            summary = course.get_attendance_summary()
            course_stats.append({
                'course_name': course.name,
                'total_classes': summary['total_records'],
                'attendance_rate': summary['attendance_rate']
            })
        
        stats['course_stats'] = course_stats
    
    return render_template("main/profile.html", stats=stats)

@main_bp.route("/about")
def about():
    """About page"""
    return render_template("main/about.html")

@main_bp.route("/contact")
def contact():
    """Contact page"""
    return render_template("main/contact.html")
