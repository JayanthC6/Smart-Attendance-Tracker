import smtplib
import logging
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from models import db, User, Course, Attendance, Notification
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email operations"""
    
    @staticmethod
    def send_attendance_alert(student_email, student_name, course_name, percentage):
        """Send attendance alert email to student"""
        if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
            logger.warning("Email credentials not configured. Skipping email.")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.MAIL_USERNAME
            msg['To'] = student_email
            msg['Subject'] = "Low Attendance Warning - Smart Attendance Tracker"
            
            # Create HTML email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h2 style="margin: 0;">Smart Attendance Tracker</h2>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">Bangalore Institute of Technology</p>
                    </div>
                    
                    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h3 style="color: #e74c3c; margin-top: 0;">Attendance Alert</h3>
                        
                        <p>Dear <strong>{student_name}</strong>,</p>
                        
                        <p>This is an automated reminder regarding your attendance for the course:</p>
                        
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Course:</strong> {course_name}</p>
                            <p style="margin: 5px 0 0 0;"><strong>Current Attendance:</strong> <span style="color: #e74c3c; font-weight: bold;">{percentage:.2f}%</span></p>
                            <p style="margin: 5px 0 0 0;"><strong>Required Threshold:</strong> {Config.ATTENDANCE_THRESHOLD}%</p>
                        </div>
                        
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0; color: #856404;"><strong>⚠️ Important:</strong> Your attendance is below the required {Config.ATTENDANCE_THRESHOLD}% threshold. Please contact your respective mentor or professor immediately.</p>
                        </div>
                        
                        <p>We encourage you to:</p>
                        <ul>
                            <li>Attend all remaining classes</li>
                            <li>Contact your faculty for any concerns</li>
                            <li>Check your attendance regularly</li>
                        </ul>
                        
                        <p>Best regards,<br>
                        <strong>Smart Attendance Tracker System</strong><br>
                        Bangalore Institute of Technology</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as smtp_server:
                smtp_server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                smtp_server.sendmail(Config.MAIL_USERNAME, student_email, msg.as_string())
            
            logger.info(f"Attendance alert sent to {student_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {student_email}: {e}")
            return False

class AttendanceService:
    """Service for handling attendance operations"""
    
    @staticmethod
    def check_and_send_alerts(course_id, start_date=None, end_date=None):
        """Check attendance and send alerts for low attendance"""
        try:
            course = Course.query.get(course_id)
            if not course:
                return
            
            # Use default period if not specified
            if not start_date or not end_date:
                end_date = date.today()
                start_date = end_date - timedelta(days=Config.ALERT_PERIOD_DAYS)
            
            students = User.query.filter_by(role='student', is_active=True).all()
            email_service = EmailService()
            
            for student in students:
                percentage = student.get_attendance_percentage(course_id, start_date, end_date)
                
                if percentage < Config.ATTENDANCE_THRESHOLD and percentage > 0:
                    # Send email alert
                    email_sent = email_service.send_attendance_alert(
                        student.email, 
                        student.full_name, 
                        course.name, 
                        percentage
                    )
                    
                    # Create notification record
                    notification = Notification(
                        user_id=student.id,
                        title="Low Attendance Alert",
                        message=f"Your attendance for {course.name} is {percentage:.2f}% (below {Config.ATTENDANCE_THRESHOLD}%)",
                        type="attendance_alert"
                    )
                    db.session.add(notification)
            
            db.session.commit()
            logger.info(f"Attendance alerts processed for course {course_id}")
            
        except Exception as e:
            logger.error(f"Error processing attendance alerts: {e}")
            db.session.rollback()

class ReportService:
    """Service for generating reports and analytics"""
    
    @staticmethod
    def get_attendance_summary(course_id=None, start_date=None, end_date=None):
        """Get comprehensive attendance summary"""
        try:
            query = db.session.query(Attendance)
            
            if course_id:
                query = query.filter(Attendance.course_id == course_id)
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
            
        except Exception as e:
            logger.error(f"Error generating attendance summary: {e}")
            return None
    
    @staticmethod
    def get_student_attendance_trend(student_id, course_id, days=30):
        """Get attendance trend for a student"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            attendance_records = db.session.query(Attendance).filter(
                Attendance.student_user_id == student_id,
                Attendance.course_id == course_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).order_by(Attendance.date).all()
            
            trend_data = []
            for record in attendance_records:
                trend_data.append({
                    'date': record.date.isoformat(),
                    'status': record.status,
                    'present': 1 if record.status == 'Present' else 0
                })
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error generating attendance trend: {e}")
            return []

class NotificationService:
    """Service for handling notifications"""
    
    @staticmethod
    def create_notification(user_id, title, message, notification_type='info'):
        """Create a new notification"""
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type
            )
            db.session.add(notification)
            db.session.commit()
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_user_notifications(user_id, limit=10):
        """Get notifications for a user"""
        try:
            return Notification.query.filter_by(
                user_id=user_id
            ).order_by(Notification.created_at.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            return []
    
    @staticmethod
    def mark_notification_read(notification_id, user_id):
        """Mark a notification as read"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=user_id
            ).first()
            
            if notification:
                notification.is_read = True
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            db.session.rollback()
            return False
