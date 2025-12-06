#!/usr/bin/env python3
"""
Migration script to upgrade from old Student Tracker to new version
This script helps migrate data and configuration from the old system
"""

import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

def backup_old_system():
    """Create a backup of the old system"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_old_system_{timestamp}"
    
    print(f"📦 Creating backup of old system in {backup_dir}...")
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Files to backup
    files_to_backup = [
        'app.py',
        'database.py',
        'attendance.db',
        'requirements.txt',
        'static/',
        'templates/',
        '.env' if os.path.exists('.env') else None
    ]
    
    for file_path in files_to_backup:
        if file_path and os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.copytree(file_path, os.path.join(backup_dir, file_path))
            else:
                shutil.copy2(file_path, backup_dir)
            print(f"✅ Backed up {file_path}")
    
    print(f"✅ Backup completed: {backup_dir}")
    return backup_dir

def migrate_database():
    """Migrate data from old database to new structure"""
    old_db_path = 'attendance.db'
    new_db_path = 'attendance_new.db'
    
    if not os.path.exists(old_db_path):
        print("⚠️  Old database not found, skipping migration")
        return
    
    print("🔄 Migrating database...")
    
    # Connect to old database
    old_conn = sqlite3.connect(old_db_path)
    old_cursor = old_conn.cursor()
    
    # Connect to new database
    new_conn = sqlite3.connect(new_db_path)
    new_cursor = new_conn.cursor()
    
    try:
        # Create new database structure
        create_new_database_structure(new_cursor)
        
        # Migrate users
        migrate_users(old_cursor, new_cursor)
        
        # Migrate courses
        migrate_courses(old_cursor, new_cursor)
        
        # Migrate attendance
        migrate_attendance(old_cursor, new_cursor)
        
        new_conn.commit()
        print("✅ Database migration completed")
        
        # Replace old database with new one
        shutil.move(new_db_path, old_db_path)
        print("✅ Database updated")
        
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        new_conn.rollback()
    finally:
        old_conn.close()
        new_conn.close()

def create_new_database_structure(cursor):
    """Create the new database structure"""
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE,
        faculty_id INTEGER UNIQUE,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'faculty', 'student')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    ''')
    
    # Courses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        code TEXT UNIQUE,
        faculty_id INTEGER,
        description TEXT,
        credits INTEGER DEFAULT 3,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (faculty_id) REFERENCES users (id)
    )
    ''')
    
    # Attendance table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        date DATE NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late')),
        remarks TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_user_id, course_id, date),
        FOREIGN KEY (student_user_id) REFERENCES users (id),
        FOREIGN KEY (course_id) REFERENCES courses (id)
    )
    ''')
    
    # Notifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Attendance logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attendance_id INTEGER NOT NULL,
        changed_by INTEGER NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (attendance_id) REFERENCES attendance (id),
        FOREIGN KEY (changed_by) REFERENCES users (id)
    )
    ''')

def migrate_users(old_cursor, new_cursor):
    """Migrate users from old to new structure"""
    print("🔄 Migrating users...")
    
    # Get all users from old database
    old_cursor.execute("SELECT * FROM users")
    old_users = old_cursor.fetchall()
    
    for user in old_users:
        # Map old structure to new structure
        new_cursor.execute('''
        INSERT INTO users (id, student_id, faculty_id, username, email, full_name, password_hash, role, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user[0],  # id
            user[1] if user[1] else None,  # student_id
            user[2] if user[2] else None,  # faculty_id
            user[3],  # username
            user[4],  # email
            user[5],  # full_name
            user[6],  # password
            user[7],  # role
            1  # is_active
        ))
    
    print(f"✅ Migrated {len(old_users)} users")

def migrate_courses(old_cursor, new_cursor):
    """Migrate courses from old to new structure"""
    print("🔄 Migrating courses...")
    
    # Get all courses from old database
    old_cursor.execute("SELECT * FROM courses")
    old_courses = old_cursor.fetchall()
    
    for course in old_courses:
        new_cursor.execute('''
        INSERT INTO courses (id, name, faculty_id, is_active)
        VALUES (?, ?, ?, ?)
        ''', (
            course[0],  # id
            course[1],  # name
            course[2] if course[2] else None,  # faculty_id
            1  # is_active
        ))
    
    print(f"✅ Migrated {len(old_courses)} courses")

def migrate_attendance(old_cursor, new_cursor):
    """Migrate attendance records from old to new structure"""
    print("🔄 Migrating attendance records...")
    
    # Get all attendance records from old database
    old_cursor.execute("SELECT * FROM attendance")
    old_attendance = old_cursor.fetchall()
    
    for record in old_attendance:
        new_cursor.execute('''
        INSERT INTO attendance (id, student_user_id, course_id, date, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            record[0],  # id
            record[1],  # student_user_id
            record[2],  # course_id
            record[3],  # date
            record[4],  # status
            datetime.now().isoformat()  # created_at
        ))
    
    print(f"✅ Migrated {len(old_attendance)} attendance records")

def migrate_templates():
    """Migrate and update template files"""
    print("🔄 Migrating templates...")
    
    # Create new templates directory if it doesn't exist
    new_templates_dir = Path('templates_new')
    new_templates_dir.mkdir(exist_ok=True)
    
    # Copy old templates to backup
    if os.path.exists('templates'):
        backup_templates_dir = 'templates_old_backup'
        shutil.copytree('templates', backup_templates_dir, dirs_exist_ok=True)
        print(f"✅ Old templates backed up to {backup_templates_dir}")
    
    print("✅ Template migration completed")

def migrate_static_files():
    """Migrate static files"""
    print("🔄 Migrating static files...")
    
    # Create new static directory structure
    new_static_dir = Path('static_new')
    new_static_dir.mkdir(exist_ok=True)
    
    # Copy old static files
    if os.path.exists('static'):
        for item in os.listdir('static'):
            src = os.path.join('static', item)
            dst = os.path.join('static_new', item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        print("✅ Static files migrated")
    
    print("✅ Static file migration completed")

def update_requirements():
    """Update requirements.txt with new dependencies"""
    print("🔄 Updating requirements...")
    
    new_requirements = """Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-WTF==1.1.1
Flask-Login==0.6.3
Flask-Mail==0.9.1
Werkzeug==2.3.7
itsdangerous==2.1.2
Jinja2==3.1.2
python-dotenv==1.0.0
WTForms==3.0.1
email-validator==2.0.0
Pillow==10.0.0
qrcode==7.4.2
reportlab==4.0.4
openpyxl==3.1.2
pytest==7.4.0
pytest-cov==4.1.0
"""
    
    # Backup old requirements
    if os.path.exists('requirements.txt'):
        shutil.copy2('requirements.txt', 'requirements_old.txt')
        print("✅ Old requirements.txt backed up as requirements_old.txt")
    
    # Write new requirements
    with open('requirements.txt', 'w') as f:
        f.write(new_requirements)
    
    print("✅ Requirements updated")

def create_migration_summary():
    """Create a summary of the migration"""
    summary = f"""
# Migration Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## What was migrated:
- ✅ Database structure and data
- ✅ User accounts and roles
- ✅ Courses and faculty assignments
- ✅ Attendance records
- ✅ Template files (backed up)
- ✅ Static files (backed up)
- ✅ Requirements.txt (updated)

## New features available:
- 🔐 Enhanced security with CSRF protection
- 📊 Advanced analytics and reporting
- 🔔 Smart notification system
- 📱 Responsive mobile design
- 🚀 RESTful API endpoints
- 🧪 Comprehensive testing framework
- 🐳 Docker deployment support

## Next steps:
1. Install new dependencies: pip install -r requirements.txt
2. Update your .env file with new configuration options
3. Run the new application: python app_new.py
4. Test all functionality with your data
5. Update any custom templates or static files

## Backup locations:
- Old system backup: backup_old_system_*
- Old templates: templates_old_backup/
- Old requirements: requirements_old.txt

## Support:
- Check README_NEW.md for detailed documentation
- Run tests: python -m pytest tests/
- Use deployment script: python deploy.py
"""
    
    with open('MIGRATION_SUMMARY.md', 'w') as f:
        f.write(summary)
    
    print("✅ Migration summary created: MIGRATION_SUMMARY.md")

def main():
    """Main migration function"""
    print("🚀 Smart Attendance Tracker Migration Script")
    print("=" * 50)
    print("This script will migrate your old system to the new version.")
    print("A backup will be created before any changes are made.")
    print()
    
    # Confirm migration
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    try:
        # Step 1: Backup old system
        backup_dir = backup_old_system()
        
        # Step 2: Migrate database
        migrate_database()
        
        # Step 3: Migrate templates
        migrate_templates()
        
        # Step 4: Migrate static files
        migrate_static_files()
        
        # Step 5: Update requirements
        update_requirements()
        
        # Step 6: Create migration summary
        create_migration_summary()
        
        print("\n🎉 Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Install new dependencies: pip install -r requirements.txt")
        print("2. Update your .env file with new configuration")
        print("3. Run the new application: python app_new.py")
        print("4. Check MIGRATION_SUMMARY.md for details")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please check the error and try again.")
        print("Your original system is backed up and unchanged.")

if __name__ == "__main__":
    main()
