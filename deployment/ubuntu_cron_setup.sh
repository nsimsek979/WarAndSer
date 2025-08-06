#!/bin/bash
# Ubuntu Service Notification Setup Script
# WarAndSer için cron ve celery servislerini kurar ve baslatir

echo "=== WarAndSer Ubuntu Service Notification Setup ==="
echo ""

# Komut kontrol fonksiyonu
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Root olarak çalistirilma kontrolü
if [ "$EUID" -ne 0 ]; then
    echo "Lütfen scripti sudo ile çalistirin."
    exit 1
fi

echo "1. Redis kurulumu kontrol ediliyor..."
if ! command_exists redis-server; then
    echo "Redis yok, kuruluyor..."
    apt-get update
    apt-get install -y redis-server
    systemctl enable redis-server
    systemctl start redis-server
    echo "? Redis kuruldu ve baslatildi."
else
    echo "? Redis zaten kurulu."
fi

echo ""
echo "2. Python bagimliliklari yükleniyor (pip)..."
# Burada pip'i venv içinden çalistirmak en iyisi
if [ -x /var/www/warandser/venv/bin/pip ]; then
    /var/www/warandser/venv/bin/pip install redis celery python-dotenv
else
    echo "? Pip bulunamadi: /var/www/warandser/venv/bin/pip"
fi

echo ""
echo "3. Celery systemd servis dosyalari olusturuluyor..."

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

echo "? Celery servis dosyalari olusturuldu."

echo ""
echo "4. Servisler etkinlestiriliyor ve baslatiliyor..."
systemctl daemon-reload
systemctl enable warandser-celery
systemctl enable warandser-celerybeat
systemctl start warandser-celery
systemctl start warandser-celerybeat

echo "? Celery servisleri çalisiyor."

echo ""
echo "5. Cron görevleri /etc/cron.d/warandser-notifications dosyasina yaziliyor..."
cat > /etc/cron.d/warandser-notifications << EOF
# WarAndSer Service Due Notifications

# Günlük bildirimler saat 09:00'da
0 9 * * * www-data cd /var/www/warandser && /var/www/warandser/venv/bin/python manage.py send_service_due_notifications --days 15 7 3 0

# Haftalik özet her Pazartesi saat 08:00'de
0 8 * * 1 www-data cd /var/www/warandser && /var/www/warandser/venv/bin/python manage.py send_weekly_service_summary

# Saglik kontrolü her saat basi
0 * * * * www-data curl -s http://localhost/warranty-and-services/api/notifications/status/ > /dev/null
EOF

echo "? Cron görevleri ayarlandi."

echo ""
echo "6. Log klasörü olusturuluyor..."
mkdir -p /var/log/warandser
chown -R www-data:www-data /var/log/warandser
echo "? Log dizini hazir."

echo ""
echo "7. Testler yapiliyor..."

echo "API durum kontrolü (curl)..."
curl -X GET http://localhost/warranty-and-services/api/notifications/status/ || echo "API endpoint erisilemedi."

echo ""
echo "Django komut testi (dry-run)..."
sudo -u www-data /var/www/warandser/venv/bin/python /var/www/warandser/manage.py send_service_due_notifications --dry-run --days 7 || echo "Django komutu çalistirilamadi."

echo ""
echo "=== Kurulum Tamamlandi ==="
echo ""
echo "Celery servis durumu:"
systemctl status warandser-celery --no-pager -l
systemctl status warandser-celerybeat --no-pager -l

echo ""
echo "Servisleri izlemek için:"
echo "  systemctl status warandser-celery"
echo "  systemctl status warandser-celerybeat"
echo "  tail -f /var/log/warandser/django.log"
echo ""
echo "Bildirimleri manuel test etmek için:"
echo "  curl -X GET http://localhost/warranty-and-services/api/notifications/status/"
echo "  sudo -u www-data /var/www/warandser/venv/bin/python /var/www/warandser/manage.py send_service_due_notifications --dry-run"
