#!/usr/bin/env python3
"""
Production setup script for Smart Attendance Tracker
Configures the application for production deployment with security, performance, and monitoring
"""

import os
import sys
import subprocess
import secrets
import string
from pathlib import Path

def generate_secret_key(length=64):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_production_env():
    """Create production environment configuration"""
    print("🔧 Creating production environment configuration...")
    
    secret_key = generate_secret_key()
    csrf_key = generate_secret_key(32)
    
    prod_env_content = f"""# Production Environment Configuration
# Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Flask Configuration
FLASK_ENV=production
DEBUG=False
SECRET_KEY={secret_key}
CSRF_SECRET_KEY={csrf_key}

# Database Configuration
DATABASE_URL=postgresql://attendance_user:secure_password@localhost:5432/attendance_db

# Email Configuration
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USER=your_production_email@domain.com
EMAIL_PASSWORD=your_production_email_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False

# Security Configuration
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=3600

# Application Configuration
HOST=0.0.0.0
PORT=5000
MAX_CONTENT_LENGTH=16777216  # 16MB

# Attendance Configuration
ATTENDANCE_THRESHOLD=75
ALERT_PERIOD_DAYS=15

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=change_this_secure_password

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Performance Configuration
SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE=20
SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW=30
SQLALCHEMY_ENGINE_OPTIONS_POOL_TIMEOUT=30
SQLALCHEMY_ENGINE_OPTIONS_POOL_RECYCLE=3600

# Cache Configuration
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
RATELIMIT_DEFAULT=100 per hour
"""
    
    with open('.env.production', 'w') as f:
        f.write(prod_env_content)
    
    print("✅ Production environment file created: .env.production")
    print("⚠️  Please update the database and email credentials before deployment")

def setup_logging():
    """Setup production logging configuration"""
    print("📝 Setting up production logging...")
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create logging configuration
    logging_config = """import logging
import logging.handlers
from pathlib import Path

def setup_logging(app):
    '''Setup production logging configuration'''
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging level
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    app.logger.setLevel(getattr(logging, log_level))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    # File handler with rotation
    log_file = logs_dir / 'app.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=app.config.get('LOG_MAX_SIZE', 10485760),  # 10MB
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Error file handler
    error_file = logs_dir / 'error.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=app.config.get('LOG_MAX_SIZE', 10485760),
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Console handler for development
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
    
    # Add handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    
    # Log application startup
    app.logger.info('Application started')
"""
    
    with open('logging_config.py', 'w') as f:
        f.write(logging_config)
    
    print("✅ Logging configuration created: logging_config.py")

def create_nginx_config():
    """Create optimized nginx configuration"""
    print("🌐 Creating nginx configuration...")
    
    nginx_config = """# Nginx configuration for Smart Attendance Tracker
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Static files
    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Favicon
    location /favicon.ico {
        alias /path/to/your/app/static/img/favicon.ico;
        expires 1y;
        access_log off;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
    
    location /auth/login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    
    with open('nginx_production.conf', 'w') as f:
        f.write(nginx_config)
    
    print("✅ Nginx configuration created: nginx_production.conf")

def create_systemd_service():
    """Create systemd service for production"""
    print("⚙️  Creating systemd service...")
    
    service_content = """[Unit]
Description=Smart Attendance Tracker
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/app/venv/bin
Environment=FLASK_ENV=production
ExecStart=/path/to/your/app/venv/bin/gunicorn --bind unix:/path/to/your/app/app.sock -m 007 --workers 4 --worker-class gevent --worker-connections 1000 --max-requests 1000 --max-requests-jitter 100 --timeout 30 --keep-alive 2 --preload app_new:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/path/to/your/app/logs
ReadWritePaths=/path/to/your/app/instance

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
"""
    
    with open('attendance-tracker.service', 'w') as f:
        f.write(service_content)
    
    print("✅ Systemd service created: attendance-tracker.service")

def create_monitoring_script():
    """Create monitoring and health check script"""
    print("📊 Creating monitoring script...")
    
    monitoring_script = """#!/bin/bash
# Smart Attendance Tracker Monitoring Script

APP_DIR="/path/to/your/app"
LOG_FILE="$APP_DIR/logs/monitor.log"
HEALTH_URL="http://localhost:5000/health"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to check application health
check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")
    if [ "$response" = "200" ]; then
        log_message "Health check: OK"
        return 0
    else
        log_message "Health check: FAILED (HTTP $response)"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    usage=$(df "$APP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 80 ]; then
        log_message "WARNING: Disk usage is ${usage}%"
    fi
}

# Function to check memory usage
check_memory() {
    usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$usage" -gt 80 ]; then
        log_message "WARNING: Memory usage is ${usage}%"
    fi
}

# Function to restart application if needed
restart_app() {
    log_message "Restarting application..."
    systemctl restart attendance-tracker
    sleep 10
    if check_health; then
        log_message "Application restarted successfully"
    else
        log_message "ERROR: Application restart failed"
    fi
}

# Main monitoring loop
main() {
    log_message "Starting monitoring check"
    
    check_disk_space
    check_memory
    
    if ! check_health; then
        restart_app
    fi
    
    log_message "Monitoring check completed"
}

# Run main function
main
"""
    
    with open('monitor.sh', 'w') as f:
        f.write(monitoring_script)
    
    # Make script executable
    os.chmod('monitor.sh', 0o755)
    
    print("✅ Monitoring script created: monitor.sh")

def create_backup_script():
    """Create database backup script"""
    print("💾 Creating backup script...")
    
    backup_script = """#!/bin/bash
# Smart Attendance Tracker Backup Script

APP_DIR="/path/to/your/app"
BACKUP_DIR="/path/to/backups"
DB_NAME="attendance_db"
DB_USER="attendance_user"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/db_backup_$DATE.sql"

# Application files backup
tar -czf "$BACKUP_DIR/app_backup_$DATE.tar.gz" -C "$APP_DIR" \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=logs \
    --exclude=.git \
    .

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
"""
    
    with open('backup.sh', 'w') as f:
        f.write(backup_script)
    
    # Make script executable
    os.chmod('backup.sh', 0o755)
    
    print("✅ Backup script created: backup.sh")

def create_security_hardening():
    """Create security hardening guide"""
    print("🔒 Creating security hardening guide...")
    
    security_guide = """# Security Hardening Guide for Smart Attendance Tracker

## 1. Server Security

### Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### SSH Security
```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Use key-based authentication
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart sshd
```

## 2. Application Security

### Environment Variables
- Use strong, unique secret keys
- Store sensitive data in environment variables
- Never commit .env files to version control

### Database Security
- Use strong database passwords
- Limit database user permissions
- Enable SSL for database connections
- Regular security updates

### File Permissions
```bash
# Set proper file permissions
chmod 600 .env.production
chmod 755 logs/
chmod 644 *.py
```

## 3. SSL/TLS Configuration

### Let's Encrypt SSL Certificate
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 4. Monitoring and Logging

### Log Monitoring
- Monitor application logs for errors
- Set up log rotation
- Monitor failed login attempts
- Track suspicious activities

### System Monitoring
- Monitor CPU and memory usage
- Monitor disk space
- Set up alerts for system issues
- Regular security updates

## 5. Backup Strategy

### Database Backups
- Daily automated backups
- Test backup restoration
- Store backups securely
- Encrypt sensitive backups

### Application Backups
- Regular code backups
- Configuration backups
- Document recovery procedures

## 6. Access Control

### User Management
- Strong password policies
- Regular password changes
- Account lockout policies
- Role-based access control

### API Security
- Rate limiting
- Input validation
- CSRF protection
- Secure session management

## 7. Regular Maintenance

### Security Updates
- Keep system packages updated
- Update application dependencies
- Monitor security advisories
- Regular security audits

### Performance Monitoring
- Monitor application performance
- Optimize database queries
- Monitor resource usage
- Regular performance testing
"""
    
    with open('SECURITY_GUIDE.md', 'w') as f:
        f.write(security_guide)
    
    print("✅ Security hardening guide created: SECURITY_GUIDE.md")

def create_deployment_checklist():
    """Create deployment checklist"""
    print("📋 Creating deployment checklist...")
    
    checklist = """# Production Deployment Checklist

## Pre-Deployment

### Environment Setup
- [ ] Server provisioned and configured
- [ ] Domain name configured
- [ ] SSL certificate obtained
- [ ] Database server configured
- [ ] Email service configured

### Application Preparation
- [ ] Code tested in staging environment
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Static files collected

### Security
- [ ] Firewall configured
- [ ] SSH security hardened
- [ ] Strong passwords set
- [ ] File permissions configured
- [ ] SSL/TLS configured

## Deployment

### Application Deployment
- [ ] Code deployed to production server
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Database initialized/migrated
- [ ] Application started

### Web Server Configuration
- [ ] Nginx installed and configured
- [ ] SSL certificate installed
- [ ] Reverse proxy configured
- [ ] Static files served correctly
- [ ] Gzip compression enabled

### Service Configuration
- [ ] Systemd service created
- [ ] Service enabled and started
- [ ] Auto-start configured
- [ ] Health checks working

## Post-Deployment

### Testing
- [ ] Application accessible via HTTPS
- [ ] All user roles can log in
- [ ] Attendance functionality works
- [ ] Email notifications working
- [ ] API endpoints responding

### Monitoring
- [ ] Logging configured
- [ ] Monitoring scripts deployed
- [ ] Backup scripts configured
- [ ] Alert systems set up
- [ ] Performance monitoring active

### Documentation
- [ ] Deployment documented
- [ ] Maintenance procedures documented
- [ ] Backup procedures documented
- [ ] Recovery procedures documented
- [ ] Contact information updated

## Maintenance

### Regular Tasks
- [ ] Security updates applied
- [ ] Database backups verified
- [ ] Log files rotated
- [ ] Performance monitored
- [ ] User feedback collected

### Monthly Tasks
- [ ] Security audit performed
- [ ] Performance review conducted
- [ ] Backup restoration tested
- [ ] Documentation updated
- [ ] Dependencies updated

## Emergency Procedures

### Incident Response
- [ ] Incident response plan documented
- [ ] Contact information available
- [ ] Rollback procedures tested
- [ ] Communication plan ready
- [ ] Recovery procedures documented
"""
    
    with open('DEPLOYMENT_CHECKLIST.md', 'w') as f:
        f.write(checklist)
    
    print("✅ Deployment checklist created: DEPLOYMENT_CHECKLIST.md")

def main():
    """Main production setup function"""
    print("🚀 Smart Attendance Tracker Production Setup")
    print("=" * 50)
    print("This script will create production configuration files.")
    print()
    
    try:
        # Create production environment
        create_production_env()
        
        # Setup logging
        setup_logging()
        
        # Create nginx configuration
        create_nginx_config()
        
        # Create systemd service
        create_systemd_service()
        
        # Create monitoring script
        create_monitoring_script()
        
        # Create backup script
        create_backup_script()
        
        # Create security hardening guide
        create_security_hardening()
        
        # Create deployment checklist
        create_deployment_checklist()
        
        print("\n🎉 Production setup completed successfully!")
        print("\n📋 Created files:")
        print("- .env.production (Production environment configuration)")
        print("- logging_config.py (Logging configuration)")
        print("- nginx_production.conf (Nginx configuration)")
        print("- attendance-tracker.service (Systemd service)")
        print("- monitor.sh (Monitoring script)")
        print("- backup.sh (Backup script)")
        print("- SECURITY_GUIDE.md (Security hardening guide)")
        print("- DEPLOYMENT_CHECKLIST.md (Deployment checklist)")
        
        print("\n⚠️  Important next steps:")
        print("1. Update .env.production with your actual configuration")
        print("2. Update file paths in all configuration files")
        print("3. Follow the SECURITY_GUIDE.md for security hardening")
        print("4. Use DEPLOYMENT_CHECKLIST.md for deployment")
        print("5. Test all configurations in a staging environment first")
        
    except Exception as e:
        print(f"\n❌ Production setup failed: {e}")
        print("Please check the error and try again.")

if __name__ == "__main__":
    main()
