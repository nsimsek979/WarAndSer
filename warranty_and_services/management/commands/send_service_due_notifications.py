from django.core.management.base import BaseCommand
from django.utils import timezone
from warranty_and_services.models import ServiceFollowUp
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send notification emails for services due in 15, 7, 3 days and on due date.'

    def handle(self, *args, **options):
        days_list = [15, 7, 3, 0]
        total_count = 0
        for days in days_list:
            target_date = timezone.now() + timedelta(days=days)
            due_services = ServiceFollowUp.objects.filter(
                is_completed=False,
                next_service_date__date=target_date.date()
            )
            count = 0
            for service in due_services:
                service.send_service_due_notification(days_before=days)
                count += 1
            if count > 0:
                self.stdout.write(self.style.SUCCESS(f'Sent notifications for {count} service(s) due in {days} day(s).'))
            total_count += count
        if total_count == 0:
            self.stdout.write(self.style.WARNING('No service due notifications sent.'))
