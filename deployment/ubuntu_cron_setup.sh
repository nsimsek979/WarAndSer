#!/bin/bash
# Ubuntu cron script for service due notifications
# Place this in /etc/cron.d/warandser-notifications

# Send service notifications daily at 9:00 AM
0 9 * * * www-data cd /var/www/warandser && /var/www/warandser/venv/bin/python manage.py send_service_due_notifications --days 15 7 3 0

# Send weekly summary on Monday at 8:00 AM  
0 8 * * 1 www-data cd /var/www/warandser && /var/www/warandser/venv/bin/python manage.py send_weekly_service_summary

# Test notifications (remove after testing)
# */5 * * * * www-data cd /var/www/warandser && /var/www/warandser/venv/bin/python manage.py send_service_due_notifications --dry-run
