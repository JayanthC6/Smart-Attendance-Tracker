import sqlite3
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

class User(db.Model):
    """User model for students, faculty, and admin"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, unique=True, nullable=True)
    faculty_id = db.Column(db.Integer, unique=True, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    courses = db.relationship('Course', backref='faculty', lazy=True)
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def get_attendance_percentage(self, course_id, start_date=None, end_date=None):
        """Calculate attendance percentage for a course"""
        query = db.session.query(Attendance).filter(
            Attendance.student_user_id == self.id,
            Attendance.course_id == course_id
        )
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
            
        total_classes = query.count()
        present_classes = query.filter(Attendance.status == 'Present').count()
        
        if total_classes == 0:
            return 0
        return (present_classes / total_classes) * 100
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'faculty_id': self.faculty_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Course(db.Model):
    """Course model"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    credits = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='course', lazy=True)
    
    def get_total_classes(self, start_date=None, end_date=None):
        """Get total number of classes for this course"""
        query = db.session.query(Attendance.date).filter(
            Attendance.course_id == self.id
        ).distinct()
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
            
        return query.count()
    
    def get_attendance_summary(self, start_date=None, end_date=None):
        """Get attendance summary for this course"""
        query = db.session.query(Attendance).filter(
            Attendance.course_id == self.id
        )
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
            
        total_records = query.count()
        present_records = query.filter(Attendance.status == 'Present').count()
        absent_records = total_records - present_records
        
        return {
            'total_records': total_records,
            'present_records': present_records,
            'absent_records': absent_records,
            'attendance_rate': (present_records / total_records * 100) if total_records > 0 else 0
        }
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'faculty_id': self.faculty_id,
            'description': self.description,
            'credits': self.credits,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Attendance(db.Model):
    """Attendance model"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'Present', 'Absent', 'Late'
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('student_user_id', 'course_id', 'date', name='unique_attendance'),)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_user_id': self.student_user_id,
            'course_id': self.course_id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AttendanceLog(db.Model):
    """Log for attendance changes"""
    __tablename__ = 'attendance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    attendance_id = db.Column(db.Integer, db.ForeignKey('attendance.id'), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance = db.relationship('Attendance', backref='logs')
    user = db.relationship('User', backref='attendance_logs')

class Notification(db.Model):
    """Notification model for alerts and messages"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'attendance_alert', 'system', 'info'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
