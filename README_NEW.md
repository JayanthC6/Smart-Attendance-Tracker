# 🎓 Smart Attendance Tracker

A comprehensive, modern attendance management system for educational institutions built with Flask and SQLAlchemy.

## ✨ Features

### 🔐 **Security & Authentication**
- **Role-based access control** (Admin, Faculty, Student)
- **Secure password hashing** with Werkzeug
- **CSRF protection** for all forms
- **Session management** with Flask-Login
- **Environment variable configuration** for sensitive data

### 📊 **Attendance Management**
- **Real-time attendance tracking** with instant updates
- **Bulk attendance operations** for efficiency
- **Attendance modification** with audit trails
- **Automated low attendance alerts** via email
- **QR code attendance system** (coming soon)

### 📈 **Analytics & Reporting**
- **Interactive dashboards** with Chart.js
- **Comprehensive reports** with date filtering
- **Attendance trends** and analytics
- **Export functionality** (PDF, Excel, CSV)
- **Real-time statistics** and insights

### 🔔 **Notifications & Alerts**
- **Smart notification system** with real-time updates
- **Email alerts** for low attendance
- **In-app notifications** with read/unread status
- **Automated reminder system**

### 🎨 **Modern UI/UX**
- **Responsive design** for all devices
- **Dark mode support** (system preference)
- **Modern Bootstrap 5** interface
- **Font Awesome icons** throughout
- **Smooth animations** and transitions
- **Accessibility features** for better usability

### 🚀 **Advanced Features**
- **RESTful API** for mobile app integration
- **Database indexing** for optimal performance
- **Background task processing**
- **Comprehensive logging** system
- **Error handling** and recovery
- **Data validation** at all levels

## 🛠️ Technology Stack

- **Backend**: Flask 2.3.3, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5, Chart.js, Font Awesome
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Security**: CSRF protection, secure sessions, password hashing
- **Email**: SMTP integration with HTML templates
- **API**: RESTful endpoints with JSON responses

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for version control)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Student-Tracker
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:
```env
# Database Configuration
DATABASE_URL=attendance.db

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_USE_TLS=True

# Security Configuration
SECRET_KEY=your_very_long_and_random_secret_key_here
CSRF_SECRET_KEY=your_csrf_secret_key_here

# Application Configuration
DEBUG=True
HOST=127.0.0.1
PORT=5000

# Attendance Configuration
ATTENDANCE_THRESHOLD=75
ALERT_PERIOD_DAYS=15

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
```

### 5. Initialize Database
```bash
python database_new.py
```

### 6. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 👥 Default Login Credentials

### Admin
- **Username**: `admin`
- **Password**: `admin123`

### Faculty
- **Username**: `faculty1`
- **Password**: `faculty123`

### Student
- **Username**: `student1`
- **Password**: `student123`

## 📱 User Roles & Permissions

### 👨‍💼 **Admin**
- Manage users (students, faculty)
- Manage courses and assignments
- View comprehensive reports
- System configuration
- Access to all features

### 👨‍🏫 **Faculty**
- Take attendance for assigned courses
- Modify attendance records
- View course-specific reports
- Manage their courses
- Send notifications to students

### 👨‍🎓 **Student**
- View personal attendance records
- Track attendance trends
- Receive notifications
- View course details
- Export personal reports

## 🗄️ Database Schema

### Users Table
- **id**: Primary key
- **student_id**: Unique student identifier
- **faculty_id**: Unique faculty identifier
- **username**: Unique username
- **email**: Unique email address
- **full_name**: Full name
- **password_hash**: Hashed password
- **role**: User role (admin/faculty/student)
- **is_active**: Account status
- **created_at**: Account creation timestamp

### Courses Table
- **id**: Primary key
- **name**: Course name
- **code**: Course code
- **faculty_id**: Assigned faculty
- **description**: Course description
- **credits**: Credit hours
- **is_active**: Course status
- **created_at**: Course creation timestamp

### Attendance Table
- **id**: Primary key
- **student_user_id**: Student reference
- **course_id**: Course reference
- **date**: Attendance date
- **status**: Present/Absent/Late
- **remarks**: Additional notes
- **created_at**: Record creation timestamp
- **updated_at**: Last update timestamp

### Notifications Table
- **id**: Primary key
- **user_id**: User reference
- **title**: Notification title
- **message**: Notification content
- **type**: Notification type
- **is_read**: Read status
- **created_at**: Creation timestamp

## 🔧 Configuration

### Environment Variables
All configuration is handled through environment variables for security and flexibility:

- **Database**: Configure database connection
- **Email**: SMTP settings for notifications
- **Security**: Secret keys and CSRF protection
- **Application**: Debug mode, host, port settings
- **Attendance**: Thresholds and alert periods

### Email Configuration
For Gmail SMTP:
1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use the app password in `EMAIL_PASSWORD`

## 📊 API Endpoints

### Authentication
- `POST /auth/login` - Admin login
- `POST /auth/student_login` - Student login
- `POST /auth/faculty_login` - Faculty login
- `POST /auth/register` - Student registration
- `GET /auth/logout` - Logout

### API Routes
- `GET /api/attendance/summary` - Get attendance summary
- `GET /api/attendance/trend/<course_id>` - Get attendance trend
- `GET /api/courses` - Get courses list
- `GET /api/students` - Get students list (admin only)
- `POST /api/attendance/bulk` - Bulk attendance entry
- `GET /api/notifications` - Get user notifications

## 🚀 Deployment

### Production Deployment

1. **Set Environment Variables**:
```bash
export FLASK_ENV=production
export SECRET_KEY=your_production_secret_key
export DATABASE_URL=postgresql://user:pass@localhost/attendance_db
```

2. **Install Production Dependencies**:
```bash
pip install gunicorn psycopg2-binary
```

3. **Run with Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app_new:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app_new:app"]
```

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/
```

### Test Coverage
```bash
python -m pytest --cov=app tests/
```

## 📈 Performance Optimization

### Database Indexing
- User role and ID indexes
- Attendance date and course indexes
- Notification user and read status indexes

### Caching
- Session-based caching for user data
- Query result caching for reports
- Static file caching

### Monitoring
- Application logging
- Performance metrics
- Error tracking

## 🔒 Security Features

- **CSRF Protection**: All forms protected
- **SQL Injection Prevention**: SQLAlchemy ORM
- **XSS Protection**: Template auto-escaping
- **Secure Sessions**: Flask-Login integration
- **Password Security**: Werkzeug hashing
- **Input Validation**: Server-side validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🎯 Roadmap

### Upcoming Features
- [ ] Mobile app (React Native)
- [ ] QR code attendance
- [ ] Biometric integration
- [ ] Advanced analytics
- [ ] Multi-language support
- [ ] Calendar integration
- [ ] SMS notifications
- [ ] Parent portal

### Version History
- **v2.0.0**: Complete rewrite with modern architecture
- **v1.0.0**: Initial release with basic features

---

**Built with ❤️ for educational institutions**
