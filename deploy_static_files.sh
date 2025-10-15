#!/bin/bash

# Ubuntu sunucuda static files için gerekli komutlar
# Bu scripti sunucuda çalıştırın

echo "=== Django Static Files Deployment ==="

# 1. Collectstatic komutunu çalıştır
echo "1. Collecting static files..."
python manage.py collectstatic --noinput

# 2. Static files dizininin izinlerini ayarla
echo "2. Setting static files permissions..."
sudo chown -R www-data:www-data staticfiles/
sudo chmod -R 755 staticfiles/

# 3. Media files dizininin izinlerini ayarla
echo "3. Setting media files permissions..."
sudo chown -R www-data:www-data media/
sudo chmod -R 755 media/

# 4. Nginx'i yeniden başlat
echo "4. Restarting Nginx..."
sudo systemctl restart nginx

# 5. Gunicorn'u yeniden başlat
echo "5. Restarting Gunicorn..."
sudo systemctl restart gunicorn

echo "=== Deployment Complete ==="
echo "Admin CSS should now be working!"
