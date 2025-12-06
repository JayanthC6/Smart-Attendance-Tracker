from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User
from services import NotificationService

auth_bp = Blueprint('auth', __name__)

def handle_login(role_to_check):
    """Helper function to handle login logic"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter(
            (User.username == username) | (User.email == username),
            User.role == role_to_check,
            User.is_active == True
        ).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Logged in successfully!', 'success')
            
            # Create welcome notification
            NotificationService.create_notification(
                user.id,
                "Welcome Back!",
                f"Welcome back, {user.full_name}! You have successfully logged in.",
                "info"
            )
            
            return redirect(url_for("main.index"))
        else:
            flash("Invalid credentials or role mismatch.", "danger")
    
    return None

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login"""
    response = handle_login('admin')
    if response:
        return response
    return render_template("auth/login.html", role="Admin")

@auth_bp.route("/student_login", methods=["GET", "POST"])
def student_login():
    """Student login"""
    response = handle_login('student')
    if response:
        return response
    return render_template("auth/student_login.html", role="Student")

@auth_bp.route("/faculty_login", methods=["GET", "POST"])
def faculty_login():
    """Faculty login"""
    response = handle_login('faculty')
    if response:
        return response
    return render_template("auth/faculty_login.html", role="Faculty")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Student registration"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('auth/register.html')
        
        try:
            # Generate student ID
            result = db.session.query(db.func.max(User.student_id)).scalar()
            next_id = (result or 0) + 1
            
            # Create new user
            user = User(
                student_id=next_id,
                username=username,
                email=email,
                full_name=full_name,
                role='student',
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.student_login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route("/logout")
@login_required
def logout():
    """Logout user"""
    user_name = current_user.full_name
    logout_user()
    flash(f"Goodbye, {user_name}! You have been logged out.", "info")
    return redirect(url_for("main.index"))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not current_user.check_password(current_password):
            flash('Your current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New password and confirmation do not match.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            
            # Create notification
            NotificationService.create_notification(
                current_user.id,
                "Password Changed",
                "Your password has been successfully updated.",
                "info"
            )
            
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for("main.index"))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your password.', 'danger')
    
    return render_template('auth/change_password.html')
