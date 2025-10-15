# UBUNTU SUNUCUDA ADMIN CSS SORUNU ÇÖZÜMÜ
# Bu adımları sırasıyla takip edin

## 1. PROJE DİZİNİNDE COLLECTSTATIC ÇALIŞTIRIN
cd /path/to/your/project  # Proje dizininize gidin
python manage.py collectstatic --noinput

## 2. STATIC FILES İZİNLERİNİ AYARLAYIN
sudo chown -R www-data:www-data staticfiles/
sudo chmod -R 755 staticfiles/

## 3. NGINX KONFİGÜRASYONUNU KONTROL EDİN
# /etc/nginx/sites-available/garantiveservis dosyasında şu satırların olması gerekiyor:

location /static/ {
    alias /path/to/your/project/staticfiles/;
    expires 30d;
}

location /media/ {
    alias /path/to/your/project/media/;
    expires 30d;
}

## 4. NGINX SYNTAX KONTROLÜ VE YENİDEN BAŞLATMA
sudo nginx -t  # Syntax kontrolü
sudo systemctl restart nginx

## 5. GUNICORN'U YENİDEN BAŞLATMA
sudo systemctl restart gunicorn

## 6. DJANGO SETTINGS'TE STATIC_ROOT KONTROLÜ
# settings.py dosyasında şunların olduğundan emin olun:

STATIC_URL = '/static/'
STATIC_ROOT = '/path/to/your/project/staticfiles/'  # Tam yol
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

## 7. DEBUG MODUNU KAPATIN
# Production'da DEBUG = False olmalı

## 8. ALLOWED_HOSTS AYARI
# settings.py'de domain adresinizi ekleyin:
ALLOWED_HOSTS = ['your-domain.com', 'your-server-ip']

## 9. LOG KONTROLÜ
# Nginx error logunu kontrol edin:
sudo tail -f /var/log/nginx/error.log

# Django logunu kontrol edin:
sudo tail -f /var/log/gunicorn/error.log

## 10. BROWSER CACHE TEMİZLEME
# Tarayıcı cache'ini temizleyin veya hard refresh yapın (Ctrl+F5)

## SORUN DEVAM EDİYORSA:
# 1. Browser developer tools'da 404 olan static files'ları kontrol edin
# 2. Nginx access.log'unda static file isteklerini kontrol edin
# 3. File path'lerinin doğru olduğundan emin olun

## ÖRNEK KOMUT SETİ:
# cd /var/www/garantiveservis
# python manage.py collectstatic --noinput
# sudo chown -R www-data:www-data staticfiles/
# sudo systemctl restart nginx
# sudo systemctl restart gunicorn
