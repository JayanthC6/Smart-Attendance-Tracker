import pytest
import json
from app_new import create_app
from models import db, User, Course, Attendance
from config import TestingConfig

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        admin = User(
            username='testadmin',
            email='admin@test.com',
            full_name='Test Admin',
            role='admin',
            is_active=True
        )
        admin.set_password('testpass')
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def faculty_user(app):
    """Create a faculty user for testing."""
    with app.app_context():
        faculty = User(
            username='testfaculty',
            email='faculty@test.com',
            full_name='Test Faculty',
            role='faculty',
            faculty_id=1,
            is_active=True
        )
        faculty.set_password('testpass')
        db.session.add(faculty)
        db.session.commit()
        return faculty

@pytest.fixture
def student_user(app):
    """Create a student user for testing."""
    with app.app_context():
        student = User(
            username='teststudent',
            email='student@test.com',
            full_name='Test Student',
            role='student',
            student_id=1,
            is_active=True
        )
        student.set_password('testpass')
        db.session.add(student)
        db.session.commit()
        return student

@pytest.fixture
def sample_course(app, faculty_user):
    """Create a sample course for testing."""
    with app.app_context():
        course = Course(
            name='Test Course',
            code='TC101',
            faculty_id=faculty_user.id,
            description='A test course',
            credits=3,
            is_active=True
        )
        db.session.add(course)
        db.session.commit()
        return course

class TestAuth:
    """Test authentication functionality."""
    
    def test_admin_login(self, client):
        """Test admin login."""
        response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        assert response.status_code == 302  # Redirect after login
    
    def test_faculty_login(self, client, faculty_user):
        """Test faculty login."""
        response = client.post('/auth/faculty_login', data={
            'username': faculty_user.username,
            'password': 'testpass'
        })
        assert response.status_code == 302
    
    def test_student_login(self, client, student_user):
        """Test student login."""
        response = client.post('/auth/student_login', data={
            'username': student_user.username,
            'password': 'testpass'
        })
        assert response.status_code == 302
    
    def test_invalid_login(self, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'username': 'invalid',
            'password': 'invalid'
        })
        assert b'Invalid credentials' in response.data
    
    def test_student_registration(self, client):
        """Test student registration."""
        response = client.post('/auth/register', data={
            'full_name': 'New Student',
            'email': 'newstudent@test.com',
            'username': 'newstudent',
            'password': 'testpass',
            'confirm_password': 'testpass'
        })
        assert response.status_code == 302  # Redirect after registration
        
        # Check if user was created
        user = User.query.filter_by(username='newstudent').first()
        assert user is not None
        assert user.role == 'student'

class TestDashboard:
    """Test dashboard functionality."""
    
    def test_admin_dashboard_access(self, client, admin_user):
        """Test admin dashboard access."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['role'] = admin_user.role
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data
    
    def test_faculty_dashboard_access(self, client, faculty_user):
        """Test faculty dashboard access."""
        with client.session_transaction() as sess:
            sess['user_id'] = faculty_user.id
            sess['role'] = faculty_user.role
        
        response = client.get('/faculty/dashboard')
        assert response.status_code == 200
        assert b'Faculty Dashboard' in response.data
    
    def test_student_dashboard_access(self, client, student_user):
        """Test student dashboard access."""
        with client.session_transaction() as sess:
            sess['user_id'] = student_user.id
            sess['role'] = student_user.role
        
        response = client.get('/student/dashboard')
        assert response.status_code == 200
        assert b'Student Dashboard' in response.data

class TestAttendance:
    """Test attendance functionality."""
    
    def test_take_attendance(self, client, faculty_user, student_user, sample_course):
        """Test taking attendance."""
        with client.session_transaction() as sess:
            sess['user_id'] = faculty_user.id
            sess['role'] = faculty_user.role
        
        response = client.post('/faculty/take_attendance', data={
            'course_id': sample_course.id,
            'date': '2024-01-15',
            'all_students': [str(student_user.id)],
            'present_students': [str(student_user.id)]
        })
        assert response.status_code == 302  # Redirect after submission
        
        # Check if attendance was recorded
        attendance = Attendance.query.filter_by(
            student_user_id=student_user.id,
            course_id=sample_course.id
        ).first()
        assert attendance is not None
        assert attendance.status == 'Present'
    
    def test_attendance_percentage_calculation(self, app, student_user, sample_course):
        """Test attendance percentage calculation."""
        with app.app_context():
            # Add some attendance records
            attendance1 = Attendance(
                student_user_id=student_user.id,
                course_id=sample_course.id,
                date='2024-01-15',
                status='Present'
            )
            attendance2 = Attendance(
                student_user_id=student_user.id,
                course_id=sample_course.id,
                date='2024-01-16',
                status='Absent'
            )
            db.session.add_all([attendance1, attendance2])
            db.session.commit()
            
            # Calculate percentage
            percentage = student_user.get_attendance_percentage(sample_course.id)
            assert percentage == 50.0

class TestAPI:
    """Test API endpoints."""
    
    def test_attendance_summary_api(self, client, student_user):
        """Test attendance summary API."""
        with client.session_transaction() as sess:
            sess['user_id'] = student_user.id
            sess['role'] = student_user.role
        
        response = client.get('/api/attendance/summary')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
    
    def test_courses_api(self, client, faculty_user):
        """Test courses API."""
        with client.session_transaction() as sess:
            sess['user_id'] = faculty_user.id
            sess['role'] = faculty_user.role
        
        response = client.get('/api/courses')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
    
    def test_notifications_api(self, client, student_user):
        """Test notifications API."""
        with client.session_transaction() as sess:
            sess['user_id'] = student_user.id
            sess['role'] = student_user.role
        
        response = client.get('/api/notifications')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data

class TestUserManagement:
    """Test user management functionality."""
    
    def test_create_user(self, client, admin_user):
        """Test creating a new user."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['role'] = admin_user.role
        
        response = client.post('/admin/manage_users', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'full_name': 'New User',
            'role': 'student',
            'password': 'testpass'
        })
        assert response.status_code == 302  # Redirect after creation
        
        # Check if user was created
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.role == 'student'
    
    def test_create_course(self, client, admin_user, faculty_user):
        """Test creating a new course."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['role'] = admin_user.role
        
        response = client.post('/admin/manage_courses', data={
            'name': 'New Course',
            'code': 'NC101',
            'faculty_id': faculty_user.id,
            'description': 'A new course',
            'credits': 3
        })
        assert response.status_code == 302  # Redirect after creation
        
        # Check if course was created
        course = Course.query.filter_by(name='New Course').first()
        assert course is not None
        assert course.faculty_id == faculty_user.id

class TestSecurity:
    """Test security features."""
    
    def test_csrf_protection(self, client):
        """Test CSRF protection."""
        response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        # Should fail without CSRF token
        assert response.status_code == 400
    
    def test_role_based_access(self, client, student_user):
        """Test role-based access control."""
        with client.session_transaction() as sess:
            sess['user_id'] = student_user.id
            sess['role'] = student_user.role
        
        # Student should not access admin dashboard
        response = client.get('/admin/dashboard')
        assert response.status_code == 302  # Redirect to unauthorized page
    
    def test_password_hashing(self, app):
        """Test password hashing."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@test.com',
                full_name='Test User',
                role='student'
            )
            user.set_password('testpass')
            
            assert user.password_hash != 'testpass'
            assert user.check_password('testpass') is True
            assert user.check_password('wrongpass') is False

if __name__ == '__main__':
    pytest.main([__file__])
