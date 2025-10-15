#!/usr/bin/env python
import os
import django

# Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvs.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

# Superuser bilgileri
USERNAME = 'konnektom'
EMAIL = 'nihat@konnektom.com'
PASSWORD = 'Konnektom123*'

try:
    # Önce migration'ları yap
    print("🔄 Migration'lar çalıştırılıyor...")
    call_command('migrate', verbosity=0)
    print("✅ Migration'lar tamamlandı!")

    # Superuser var mı kontrol et
    if User.objects.filter(username=USERNAME).exists():
        print(f"⚠️  Superuser '{USERNAME}' zaten mevcut!")
        # Şifreyi güncelle
        user = User.objects.get(username=USERNAME)
        user.set_password(PASSWORD)
        user.save()
        print(f"✅ Superuser '{USERNAME}' şifresi güncellendi!")
    else:
        # Yeni superuser oluştur
        User.objects.create_superuser(
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD
        )
        print(f"✅ Superuser '{USERNAME}' oluşturuldu!")

    print(f"📧 Email: {EMAIL}")
    print(f"🔑 Username: {USERNAME}")
    print(f"🔒 Password: {PASSWORD}")
    print(f"🌐 Admin URL: http://localhost/admin/")

except Exception as e:
    print(f"❌ Hata: {e}")
    print("💡 Önce database bağlantısını test edin: python test_db.py")
