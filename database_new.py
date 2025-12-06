import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app for database initialization"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    return app

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        from models import db, User, Course, Attendance, Notification, AttendanceLog
        
        # Create all tables
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Create indexes for better performance
        try:
            # Create indexes
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_users_faculty_id ON users(faculty_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student_course ON attendance(student_user_id, course_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_attendance_course_date ON attendance(course_id, date)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_courses_faculty ON courses(faculty_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)')
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
        
        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@example.com',
                full_name='System Administrator',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            logger.info("Admin user created")
        
        # Create sample faculty users
        faculty_users = [
            {
                'username': 'faculty1',
                'email': 'faculty1@example.com',
                'full_name': 'Dr. John Smith',
                'faculty_id': 1
            },
            {
                'username': 'faculty2',
                'email': 'faculty2@example.com',
                'full_name': 'Prof. Jane Doe',
                'faculty_id': 2
            },
            {
                'username': 'faculty3',
                'email': 'faculty3@example.com',
                'full_name': 'Dr. Michael Johnson',
                'faculty_id': 3
            }
        ]
        
        for faculty_data in faculty_users:
            existing_faculty = User.query.filter_by(username=faculty_data['username']).first()
            if not existing_faculty:
                faculty = User(
                    username=faculty_data['username'],
                    email=faculty_data['email'],
                    full_name=faculty_data['full_name'],
                    faculty_id=faculty_data['faculty_id'],
                    role='faculty',
                    is_active=True
                )
                faculty.set_password('faculty123')
                db.session.add(faculty)
                logger.info(f"Faculty user created: {faculty_data['full_name']}")
        
        # Create sample courses
        sample_courses = [
            {
                'name': 'Data Structures and Algorithms',
                'code': 'CS301',
                'faculty_id': 1,
                'description': 'Introduction to fundamental data structures and algorithms',
                'credits': 4
            },
            {
                'name': 'Database Management Systems',
                'code': 'CS302',
                'faculty_id': 2,
                'description': 'Database design, implementation, and management',
                'credits': 3
            },
            {
                'name': 'Web Development',
                'code': 'CS303',
                'faculty_id': 3,
                'description': 'Modern web development technologies and frameworks',
                'credits': 3
            },
            {
                'name': 'Software Engineering',
                'code': 'CS304',
                'faculty_id': 1,
                'description': 'Software development lifecycle and methodologies',
                'credits': 3
            },
            {
                'name': 'Computer Networks',
                'code': 'CS305',
                'faculty_id': 2,
                'description': 'Network protocols, architecture, and security',
                'credits': 3
            }
        ]
        
        for course_data in sample_courses:
            existing_course = Course.query.filter_by(name=course_data['name']).first()
            if not existing_course:
                course = Course(
                    name=course_data['name'],
                    code=course_data['code'],
                    faculty_id=course_data['faculty_id'],
                    description=course_data['description'],
                    credits=course_data['credits'],
                    is_active=True
                )
                db.session.add(course)
                logger.info(f"Course created: {course_data['name']}")
        
        # Create sample students
        sample_students = [
            {
                'username': 'student1',
                'email': 'student1@example.com',
                'full_name': 'Alice Johnson',
                'student_id': 1
            },
            {
                'username': 'student2',
                'email': 'student2@example.com',
                'full_name': 'Bob Smith',
                'student_id': 2
            },
            {
                'username': 'student3',
                'email': 'student3@example.com',
                'full_name': 'Carol Williams',
                'student_id': 3
            },
            {
                'username': 'student4',
                'email': 'student4@example.com',
                'full_name': 'David Brown',
                'student_id': 4
            },
            {
                'username': 'student5',
                'email': 'student5@example.com',
                'full_name': 'Eva Davis',
                'student_id': 5
            }
        ]
        
        for student_data in sample_students:
            existing_student = User.query.filter_by(username=student_data['username']).first()
            if not existing_student:
                student = User(
                    username=student_data['username'],
                    email=student_data['email'],
                    full_name=student_data['full_name'],
                    student_id=student_data['student_id'],
                    role='student',
                    is_active=True
                )
                student.set_password('student123')
                db.session.add(student)
                logger.info(f"Student user created: {student_data['full_name']}")
        
        # Commit all changes
        db.session.commit()
        logger.info("Database initialization completed successfully")
        
        # Print summary
        total_users = User.query.count()
        total_courses = Course.query.count()
        total_students = User.query.filter_by(role='student').count()
        total_faculty = User.query.filter_by(role='faculty').count()
        
        print("\n" + "="*50)
        print("DATABASE INITIALIZATION SUMMARY")
        print("="*50)
        print(f"Total Users: {total_users}")
        print(f"  - Students: {total_students}")
        print(f"  - Faculty: {total_faculty}")
        print(f"  - Admin: {User.query.filter_by(role='admin').count()}")
        print(f"Total Courses: {total_courses}")
        print("\nDefault Login Credentials:")
        print("Admin: admin / admin123")
        print("Faculty: faculty1 / faculty123")
        print("Student: student1 / student123")
        print("="*50)

def reset_database():
    """Reset database (drop and recreate all tables)"""
    app = create_app()
    
    with app.app_context():
        from models import db
        
        # Drop all tables
        db.drop_all()
        logger.info("All database tables dropped")
        
        # Recreate tables
        db.create_all()
        logger.info("All database tables recreated")
        
        # Reinitialize with sample data
        init_database()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        print("Resetting database...")
        reset_database()
    else:
        print("Initializing database...")
        init_database()
