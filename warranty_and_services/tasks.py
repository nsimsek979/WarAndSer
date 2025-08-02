"""
Celery tasks for automated service notifications
Ubuntu-compatible alternative to Windows Task Scheduler
"""

from celery import shared_task
from django.core.management import call_command
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
from warranty_and_services.models import Installation
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_daily_service_notifications():
    """
    Daily task to send service due notifications
    This replaces Windows Task Scheduler
    """
    try:
        # Send notifications for multiple day intervals
        days_list = [15, 7, 3, 0]  # 15 days, 7 days, 3 days, today
        
        logger.info(f"Starting daily service notifications for {days_list} days")
        
        total_sent = 0
        for days in days_list:
            sent_count = send_notifications_for_days(days)
            total_sent += sent_count
            
        logger.info(f"Daily service notifications completed. Total sent: {total_sent}")
        return f"Successfully sent {total_sent} notifications"
        
    except Exception as e:
        logger.error(f"Error in daily service notifications: {str(e)}")
        raise

@shared_task  
def send_notifications_for_days(days_before):
    """Send notifications for installations due in specified days"""
    
    today = timezone.now().date()
    target_date = today + timedelta(days=days_before)
    
    # Get installations with service due on target date
    installations = Installation.objects.filter(
        service_followups__next_service_date=target_date,
        service_followups__is_completed=False
    ).distinct().select_related(
        'customer',
        'inventory_item__item_master',
        'customer__related_manager'
    )
    
    sent_count = 0
    
    for installation in installations:
        try:
            if send_service_notification_email(installation, days_before):
                sent_count += 1
                
        except Exception as e:
            logger.error(f'Error sending notification for installation {installation.id}: {str(e)}')
    
    logger.info(f'Sent {sent_count} notifications for services due in {days_before} days')
    return sent_count

def send_service_notification_email(installation, days_before):
    """Send service due notification email"""
    
    try:
        # Determine notification type
        if days_before == 0:
            subject_prefix = "URGENT"
            priority = "high"
        elif days_before <= 3:
            subject_prefix = "REMINDER"
            priority = "normal"
        else:
            subject_prefix = "NOTICE"
            priority = "normal"
            
        # Get next service date
        next_service = installation.service_followups.filter(
            is_completed=False
        ).order_by('next_service_date').first()
        
        if not next_service:
            return False
            
        # Prepare email context
        context = {
            'installation': installation,
            'customer': installation.customer,
            'item': installation.inventory_item.item_master,
            'serial_number': installation.inventory_item.serial_number,
            'next_service_date': next_service.next_service_date,
            'days_before': days_before,
            'priority': priority,
            'subject_prefix': subject_prefix
        }
        
        # Render email content
        subject = f"{subject_prefix}: Service Due - {installation.customer.name} - {context['item'].name}"
        html_content = render_to_string('warranty_and_services/emails/service_due_notification.html', context)
        text_content = render_to_string('warranty_and_services/emails/service_due_notification.txt', context)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[installation.customer.email] if installation.customer.email else [],
            cc=[]
        )
        
        # Add manager to CC if exists
        if installation.customer.related_manager and installation.customer.related_manager.email:
            email.cc.append(installation.customer.related_manager.email)
            
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        if email.to or email.cc:
            email.send()
            logger.info(f"Service notification sent for {installation.customer.name} - {context['item'].name}")
            return True
        else:
            logger.warning(f"No email addresses found for {installation.customer.name}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending service notification: {str(e)}")
        return False

@shared_task
def test_service_notifications():
    """Test task to verify email functionality"""
    try:
        logger.info("Testing service notification system...")
        
        # Get one installation for testing
        installation = Installation.objects.filter(
            service_followups__is_completed=False
        ).first()
        
        if installation:
            result = send_service_notification_email(installation, 7)
            return f"Test notification sent: {result}"
        else:
            return "No installations found for testing"
            
    except Exception as e:
        logger.error(f"Error in test notifications: {str(e)}")
        raise
