#!/bin/bash
# Ubuntu Service Notification Setup Script
# Replaces Windows GTK Runtime and Task Scheduler

echo "=== WarAndSer Ubuntu Service Notification Setup ==="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

echo "1. Installing Redis for Celery (if not installed)..."
if ! command_exists redis-server; then
    apt-get update
    apt-get install -y redis-server
    systemctl enable redis-server
    systemctl start redis-server
    echo "✓ Redis installed and started"
else
    echo "✓ Redis already installed"
fi

echo ""
echo "2. Installing Python dependencies..."
pip install redis celery python-dotenv

echo ""
echo "3. Setting up Celery systemd services..."

# Create celery worker service
cat > /etc/systemd/system/warandser-celery.service << EOF
[Unit]
Description=WarAndSer Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/var/www/warandser/.env
WorkingDirectory=/var/www/warandser
ExecStart=/var/www/warandser/venv/bin/celery -A gvs worker --loglevel=info --detach
ExecStop=/var/www/warandser/venv/bin/celery -A gvs control shutdown
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create celery beat service (scheduler)
cat > /etc/systemd/system/warandser-celerybeat.service << EOF
[Unit]
Description=WarAndSer Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
EnvironmentFile=/var/www/warandser/.env
WorkingDirectory=/var/www/warandser
ExecStart=/var/www/warandser/venv/bin/celery -A gvs beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Celery systemd services created"

echo ""
echo "4. Enabling and starting services..."
systemctl daemon-reload
systemctl enable warandser-celery
systemctl enable warandser-celerybeat
systemctl start warandser-celery
systemctl start warandser-celerybeat

echo "✓ Celery services started"

echo ""
echo "5. Setting up cron backup (alternative method)..."
cat > /etc/cron.d/warandser-notifications << EOF
# WarAndSer Service Due Notifications
# Send notifications daily at 9:00 AM
0 9 * * * www-data cd /var/www/warandser && /var/www/warandser/venv/bin/python manage.py send_service_due_notifications --days 15 7 3 0

# Weekly service summary on Monday at 8:00 AM  
0 8 * * 1 www-data cd /var/www/warandser && /var/www/warandser/venv/bin/python manage.py send_weekly_service_summary

# Health check every hour
0 * * * * www-data curl -s http://localhost/warranty-and-services/api/notifications/status/ > /dev/null
EOF

echo "✓ Cron backup setup completed"

echo ""
echo "6. Creating log directories..."
mkdir -p /var/log/warandser
chown -R www-data:www-data /var/log/warandser

echo ""
echo "7. Testing service notification system..."
echo "Testing API endpoint..."
curl -X GET http://localhost/warranty-and-services/api/notifications/status/

echo ""
echo "Testing Django management command..."
sudo -u www-data /var/www/warandser/venv/bin/python /var/www/warandser/manage.py send_service_due_notifications --dry-run --days 7

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Service notification system is now running on Ubuntu!"
echo ""
echo "Services status:"
systemctl status warandser-celery --no-pager -l
systemctl status warandser-celerybeat --no-pager -l

echo ""
echo "To monitor services:"
echo "  systemctl status warandser-celery"
echo "  systemctl status warandser-celerybeat"
echo "  tail -f /var/log/warandser/django.log"
echo ""
echo "To manually test notifications:"
echo "  curl -X GET http://localhost/warranty-and-services/api/notifications/status/"
echo "  python manage.py send_service_due_notifications --dry-run"
