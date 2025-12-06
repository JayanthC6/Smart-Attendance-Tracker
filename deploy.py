#!/usr/bin/env python3
"""
Deployment script for Smart Attendance Tracker
Handles database migration, environment setup, and production deployment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        sys.exit(1)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")

def setup_virtual_environment():
    """Create and activate virtual environment"""
    if not os.path.exists('venv'):
        run_command('python -m venv venv', 'Creating virtual environment')
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = 'venv\\Scripts\\activate'
        pip_command = 'venv\\Scripts\\pip'
    else:  # Unix/Linux/macOS
        activate_script = 'source venv/bin/activate'
        pip_command = 'venv/bin/pip'
    
    return activate_script, pip_command

def install_dependencies(pip_command):
    """Install required dependencies"""
    run_command(f'{pip_command} install --upgrade pip', 'Upgrading pip')
    run_command(f'{pip_command} install -r requirements.txt', 'Installing dependencies')

def setup_environment():
    """Setup environment variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """# Database Configuration
DATABASE_URL=attendance.db

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_USE_TLS=True

# Security Configuration
SECRET_KEY=your_very_long_and_random_secret_key_here_change_in_production
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
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created. Please update with your actual values.")
    else:
        print("✅ .env file already exists")

def initialize_database():
    """Initialize the database"""
    run_command('python database_new.py', 'Initializing database')

def run_tests():
    """Run the test suite"""
    if os.path.exists('tests'):
        run_command('python -m pytest tests/ -v', 'Running tests')
    else:
        print("⚠️  No tests directory found, skipping tests")

def create_production_config():
    """Create production configuration"""
    prod_config = """# Production Configuration
FLASK_ENV=production
DEBUG=False
SECRET_KEY=change_this_to_a_very_long_random_string_in_production
DATABASE_URL=postgresql://user:password@localhost/attendance_db

# Email Configuration (Production)
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USER=your_production_email@domain.com
EMAIL_PASSWORD=your_production_password
EMAIL_USE_TLS=True

# Security
CSRF_SECRET_KEY=change_this_csrf_secret_key_in_production

# Server Configuration
HOST=0.0.0.0
PORT=5000
"""
    
    with open('.env.production', 'w') as f:
        f.write(prod_config)
    print("✅ Production configuration created (.env.production)")

def create_systemd_service():
    """Create systemd service file for Linux deployment"""
    service_content = """[Unit]
Description=Smart Attendance Tracker
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/app/venv/bin
ExecStart=/path/to/your/app/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app_new:app
Restart=always

[Install]
WantedBy=multi-user.target
"""
    
    with open('attendance-tracker.service', 'w') as f:
        f.write(service_content)
    print("✅ Systemd service file created (attendance-tracker.service)")

def create_nginx_config():
    """Create nginx configuration"""
    nginx_config = """server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
    
    with open('nginx.conf', 'w') as f:
        f.write(nginx_config)
    print("✅ Nginx configuration created (nginx.conf)")

def create_docker_files():
    """Create Docker configuration files"""
    
    # Dockerfile
    dockerfile_content = """FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app_new:app"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    # docker-compose.yml
    compose_content = """version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/attendance_db
    depends_on:
      - db
    volumes:
      - ./static:/app/static
      - ./logs:/app/logs

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=attendance_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./static:/var/www/static
    depends_on:
      - web

volumes:
  postgres_data:
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    print("✅ Docker files created (Dockerfile, docker-compose.yml)")

def main():
    """Main deployment function"""
    print("🚀 Smart Attendance Tracker Deployment Script")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Setup virtual environment
    activate_script, pip_command = setup_virtual_environment()
    
    # Install dependencies
    install_dependencies(pip_command)
    
    # Setup environment
    setup_environment()
    
    # Initialize database
    initialize_database()
    
    # Run tests
    run_tests()
    
    # Create production files
    create_production_config()
    create_systemd_service()
    create_nginx_config()
    create_docker_files()
    
    print("\n🎉 Deployment setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your actual configuration")
    print("2. Run the application: python app_new.py")
    print("3. Access the application at http://localhost:5000")
    print("\n🔧 For production deployment:")
    print("1. Update .env.production with production values")
    print("2. Use gunicorn for production: gunicorn -w 4 -b 0.0.0.0:5000 app_new:app")
    print("3. Configure nginx as reverse proxy")
    print("4. Set up SSL certificates for HTTPS")
    
    print("\n🐳 For Docker deployment:")
    print("1. docker-compose up -d")
    print("2. Access at http://localhost")

if __name__ == "__main__":
    main()
