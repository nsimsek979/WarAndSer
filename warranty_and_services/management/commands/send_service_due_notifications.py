from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
from warranty_and_services.models import Installation
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send service due notifications to customers and managers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            nargs='+',
            default=[15, 7, 3, 0],
            help='Days before service due to send notifications (default: 15, 7, 3, 0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show which notifications would be sent, without actually sending them'
        )

    def handle(self, *args, **options):
        days_list = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting service due notifications for {days_list} days...')
        )
        
        total_sent = 0
        
        for days in days_list:
            sent_count = self.send_notifications_for_days(days, dry_run)
            total_sent += sent_count
            
        self.stdout.write(
            self.style.SUCCESS(f'Total notifications sent: {total_sent}')
        )

    def send_notifications_for_days(self, days_before, dry_run=False):
        """Send notifications for installations due in specified days"""
        
        today = timezone.now().date()
        target_date = today + timedelta(days=days_before)
        
        # Get installations with service due on target date
        installations = Installation.objects.filter(
            service_followups__next_service_date__date=target_date,
            service_followups__is_completed=False
        ).distinct().select_related(
            'customer',
            'inventory_item__name',
            'customer__related_manager'
        )
        
        sent_count = 0
        
        for installation in installations:
            try:
                if dry_run:
                    self.stdout.write(
                        f'Would send notification for: {installation.customer.name} - '
                        f'{installation.inventory_item.item_master.name} (Serial: {installation.inventory_item.serial_number}) - '
                        f'Service due: {installation.next_service_date}'
                    )
                    sent_count += 1
                else:
                    if self.send_service_notification(installation, days_before):
                        sent_count += 1
                        
            except Exception as e:
                logger.error(f'Error sending notification for installation {installation.id}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'Error sending notification for installation {installation.id}: {str(e)}')
                )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Sent {sent_count} notifications for services due in {days_before} days')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Would send {sent_count} notifications for services due in {days_before} days (DRY RUN)')
            )
            
        return sent_count

    def send_service_notification(self, installation, days_before):
        """Send service due notification email"""
        
        try:
            # Determine notification type
            if days_before == 0:
                notification_type = 'due_today'
                subject_prefix = 'SERVİS GÜNÜ GELDİ'
            elif days_before == 3:
                notification_type = 'due_in_3_days'
                subject_prefix = '3 GÜN KALDI'
            elif days_before == 7:
                notification_type = 'due_in_7_days'
                subject_prefix = '1 HAFTA KALDI'
            elif days_before == 15:
                notification_type = 'due_in_15_days'
                subject_prefix = '15 GÜN KALDI'
            else:
                notification_type = 'custom'
                subject_prefix = f'{days_before} GÜN KALDI'

            # Email recipients
            recipients = []
            
            # Add customer contact email
            if installation.customer.email:
                recipients.append(installation.customer.email)
            
            # Add related manager email
            if installation.customer.related_manager and installation.customer.related_manager.email:
                recipients.append(installation.customer.related_manager.email)
            
            # Add customer contacts  
            if hasattr(installation.customer, 'contactperson_set'):
                for contact in installation.customer.contactperson_set.all():
                    if contact.email:
                        recipients.append(contact.email)
            
            if not recipients:
                logger.warning(f'No email recipients found for installation {installation.id}')
                return False
            
            # Remove duplicates
            recipients = list(set(recipients))
            
            # Email subject
            subject = f'{subject_prefix} - Servis Zamanı: {installation.customer.name} - {installation.inventory_item.name.name}'
            
            # Email context
            context = {
                'installation': installation,
                'customer': installation.customer,
                'item': installation.inventory_item.name,  # ItemMaster object
                'inventory_item': installation.inventory_item,
                'days_before': days_before,
                'notification_type': notification_type,
                'service_date': self.get_next_service_date(installation),
                'today': timezone.now().date(),
            }
            
            # Render email templates
            html_content = render_to_string('warranty_and_services/emails/service_due_notification.html', context)
            text_content = render_to_string('warranty_and_services/emails/service_due_notification.txt', context)
            
            # Create and send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.attach_alternative(html_content, "text/html")
            
            email.send()
            
            logger.info(f'Service notification sent for installation {installation.id} to {recipients}')
            
            return True
            
        except Exception as e:
            logger.error(f'Error sending service notification for installation {installation.id}: {str(e)}')
            return False

    def get_next_service_date(self, installation):
        """Get the next service date for an installation"""
        service_followup = installation.service_followups.filter(is_completed=False).order_by('next_service_date').first()
        return service_followup.next_service_date if service_followup else None

    def get_service_priority_text(self, days_before):
        """Get priority text based on days before service due"""
        if days_before == 0:
            return "ACİL - BUGÜN"
        elif days_before <= 3:
            return "YÜKSEK ÖNCELİK"
        elif days_before <= 7:
            return "ORTA ÖNCELİK"
        else:
            return "NORMAL"
