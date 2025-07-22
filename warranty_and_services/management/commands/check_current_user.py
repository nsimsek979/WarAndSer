from django.core.management.base import BaseCommand
from custom_user.models import CustomUser
from warranty_and_services.utils import get_user_accessible_companies

class Command(BaseCommand):
    help = 'Check currently logged in user and their accessible companies'

    def handle(self, *args, **options):
        # Aktif kullanıcıları listele
        users = CustomUser.objects.filter(is_active=True).select_related('company')
        
        self.stdout.write("=== Aktif Kullanıcılar ===")
        for user in users:
            self.stdout.write(f"\nKullanıcı: {user.username}")
            self.stdout.write(f"Role: {user.role}")
            self.stdout.write(f"Company: {user.company.name if user.company else 'None'}")
            self.stdout.write(f"Is Staff: {user.is_staff}")
            self.stdout.write(f"Is Superuser: {user.is_superuser}")
            self.stdout.write(f"Last Login: {user.last_login}")
            
            if user.company:
                accessible = get_user_accessible_companies(user)
                self.stdout.write(f"Accessible Companies: {accessible}")
                
        # Son giriş yapan kullanıcıları göster
        recent_users = CustomUser.objects.filter(
            is_active=True,
            last_login__isnull=False
        ).order_by('-last_login')[:5]
        
        self.stdout.write("\n=== Son Giriş Yapan 5 Kullanıcı ===")
        for user in recent_users:
            self.stdout.write(f"{user.username} - {user.last_login} - {user.company.name if user.company else 'No Company'}")
