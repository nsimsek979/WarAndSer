# IIS Deployment Guide - Django Projesi

Bu rehber, Django projesini IIS (Internet Information Services) üzerinde PostgreSQL veritabanı ile production ortamında çalıştırmak için gereken adımları açıklar.

## Gereksinimler

### 1. Yazılım Gereksinimleri
- Windows Server 2016 veya üzeri
- IIS 8.0 veya üzeri
- Python 3.10 veya üzeri
- PostgreSQL 14 veya üzeri
- Redis (opsiyonel, Celery için)

### 2. IIS Özellikleri
IIS üzerinde aşağıdaki özelliklerin etkinleştirilmesi gerekir:
- Web Server (IIS)
- CGI
- ISAPI Extensions
- ISAPI Filters
- WebSocket Protocol (opsiyonel)

## Adım 1: Python ve Paketlerin Kurulumu

### Python Kurulumu
1. Python'u indirin ve kurun: https://www.python.org/downloads/
2. Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin
3. Kurulumun doğru olduğunu kontrol edin:
   ```
   python --version
   ```

### Sanal Ortam Oluşturma
```powershell
cd C:\Konnektom\WarAndSer
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Bağımlılıkları Yükleme
```powershell
pip install -r requirements.txt
pip install wfastcgi
```

### wfastcgi'yi Etkinleştirme
```powershell
wfastcgi-enable
```
Bu komut, wfastcgi'nin yolunu gösterecek. Bu yolu `web.config` dosyasında kullanacaksınız.

## Adım 2: PostgreSQL Kurulumu ve Yapılandırması

### PostgreSQL Kurulumu
1. PostgreSQL'i indirin ve kurun: https://www.postgresql.org/download/windows/
2. pgAdmin'i açın ve yeni bir veritabanı oluşturun:

```sql
CREATE DATABASE avanti_db;
CREATE USER avanti_user WITH PASSWORD 'Konnektom*123';
ALTER ROLE avanti_user SET client_encoding TO 'utf8';
ALTER ROLE avanti_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE avanti_user SET timezone TO 'Europe/Istanbul';
GRANT ALL PRIVILEGES ON DATABASE avanti_db TO avanti_user;
```

## Adım 3: Ortam Değişkenlerini Ayarlama

### .env Dosyası Oluşturma
1. `.env.example` dosyasını `.env` olarak kopyalayın
2. `.env` dosyasını düzenleyin ve gerçek değerlerinizi girin:

```env
SECRET_KEY=çok-güçlü-ve-rastgele-bir-anahtar-buraya
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_NAME=warandser_db
DB_USER=warandser_user
DB_PASSWORD=güçlü_şifre_buraya
DB_HOST=localhost
DB_PORT=5432

STATIC_ROOT=C:\inetpub\wwwroot\warandser\static
MEDIA_ROOT=C:\inetpub\wwwroot\warandser\media
LOG_DIR=C:\inetpub\wwwroot\warandser\logs
```

**Önemli:** `.env` dosyasını asla Git'e commit etmeyin!

## Adım 4: Django Proje Ayarları

### Statik Dosyaları Toplama
```powershell
cd C:\Konnektom\WarAndSer
.\venv\Scripts\Activate.ps1
python manage.py collectstatic --noinput
```

### Veritabanı Migration'larını Çalıştırma
```powershell
# Önce mevcut migration'ları kontrol edin
python manage.py showmigrations

# Migration'ları uygulayın
python manage.py migrate

# Superuser oluşturun (opsiyonel)
python manage.py createsuperuser
```

## Adım 5: IIS Yapılandırması

### 1. Klasör İzinlerini Ayarlama
Aşağıdaki klasörlere IIS kullanıcısı (IIS_IUSRS ve IUSR) için yazma izni verin:
- `C:\inetpub\wwwroot\warandser\media`
- `C:\inetpub\wwwroot\warandser\logs`
- `C:\Konnektom\WarAndSer\db.sqlite3` (eğer SQLite kullanıyorsanız)

```powershell
icacls "C:\inetpub\wwwroot\warandser\media" /grant "IIS_IUSRS:(OI)(CI)M"
icacls "C:\inetpub\wwwroot\warandser\logs" /grant "IIS_IUSRS:(OI)(CI)M"
icacls "C:\Konnektom\WarAndSer" /grant "IIS_IUSRS:(OI)(CI)M"
```

### 2. IIS Manager'da Site Oluşturma

1. IIS Manager'ı açın
2. Sol taraftaki ağaçta "Sites"a sağ tıklayın ve "Add Website" seçin
3. Site ayarlarını yapın:
   - **Site name:** WarAndSer
   - **Physical path:** C:\Konnektom\WarAndSer
   - **Binding:**
     - Type: http
     - IP address: All Unassigned
     - Port: 80
     - Host name: yourdomain.com (isteğe bağlı)

4. "OK" butonuna tıklayın

### 3. FastCGI Ayarları

1. IIS Manager'da sunucu seviyesinde "FastCGI Settings"e çift tıklayın
2. "Add Application" butonuna tıklayın
3. Ayarları yapın:
   - **Full Path:** C:\Python312\python.exe
   - **Arguments:** C:\Python312\Lib\site-packages\wfastcgi.py
   - **Environment Variables:** Ekle butonuna tıklayarak:
     - `DJANGO_SETTINGS_MODULE` = `gvs.settings_iis_prod`
     - `PYTHONPATH` = `C:\Konnektom\WarAndSer`
     - `WSGI_HANDLER` = `django.core.wsgi.get_wsgi_application()`

4. "OK" butonuna tıklayın

### 4. web.config Dosyasını Güncelleme

`web.config` dosyasındaki yolları sisteminize göre güncelleyin:
- Python yolu
- wfastcgi.py yolu
- PYTHONPATH

### 5. Handler Mappings

1. Site seviyesinde "Handler Mappings"e çift tıklayın
2. "Add Module Mapping" butonuna tıklayın
3. Ayarları yapın:
   - **Request path:** *
   - **Module:** FastCgiModule
   - **Executable:** C:\Python312\python.exe|C:\Python312\Lib\site-packages\wfastcgi.py
   - **Name:** Python FastCGI

4. "Request Restrictions" butonuna tıklayın
5. "Invoke handler only if request is mapped to:" seçeneğini işaretleyin ve "File or Folder" seçin
6. "OK" butonlarına tıklayın

## Adım 6: Static ve Media Dosyaları için Virtual Directory

### Static Dosyalar
1. Site'ınıza sağ tıklayın
2. "Add Virtual Directory" seçin
3. Ayarları yapın:
   - **Alias:** static
   - **Physical path:** C:\inetpub\wwwroot\warandser\static
4. "OK" butonuna tıklayın

### Media Dosyalar
1. Site'ınıza sağ tıklayın
2. "Add Virtual Directory" seçin
3. Ayarları yapın:
   - **Alias:** media
   - **Physical path:** C:\inetpub\wwwroot\warandser\media
4. "OK" butonuna tıklayın

## Adım 7: URL Rewrite Modülü (İsteğe Bağlı)

URL Rewrite modülü daha iyi URL yönetimi sağlar:

1. URL Rewrite modülünü indirin ve kurun: https://www.iis.net/downloads/microsoft/url-rewrite
2. `web.config` dosyası zaten gerekli kuralları içeriyor

## Adım 8: HTTPS Yapılandırması (Production için Önerilir)

### SSL Sertifikası Alma
1. Let's Encrypt veya başka bir CA'dan SSL sertifikası alın
2. IIS Manager'da site'ınıza sağ tıklayın ve "Edit Bindings" seçin
3. "Add" butonuna tıklayın
4. Ayarları yapın:
   - **Type:** https
   - **Port:** 443
   - **SSL certificate:** Sertifikanızı seçin
5. "OK" butonuna tıklayın

### Django Ayarları
`.env` dosyasında `USE_HTTPS=True` olarak ayarlayın

## Adım 9: Test Etme

1. IIS'de site'ı başlatın
2. Tarayıcınızda `http://localhost` veya domain adresinizi açın
3. Admin paneline erişimi test edin: `http://localhost/admin`

### Hata Ayıklama

Eğer sorun yaşarsanız:

1. **Detaylı Hata Mesajlarını Gösterme:**
   ```powershell
   # .env dosyasında geçici olarak
   DEBUG=True
   ```

2. **Log Dosyalarını Kontrol Etme:**
   - `C:\inetpub\wwwroot\warandser\logs\django_error.log`
   - `C:\inetpub\wwwroot\warandser\logs\wfastcgi.log`
   - IIS Log dosyaları: `C:\inetpub\logs\LogFiles`

3. **Event Viewer'ı Kontrol Etme:**
   - Windows + R > eventvwr.msc
   - Windows Logs > Application

## Adım 10: Performans Optimizasyonu

### 1. Application Pool Ayarları
1. IIS Manager'da "Application Pools"u açın
2. Site'ınızın pool'una sağ tıklayın ve "Advanced Settings" seçin
3. Önerilen ayarlar:
   - **Start Mode:** AlwaysRunning
   - **Idle Time-out:** 0 (disable)
   - **Maximum Worker Processes:** 2 veya daha fazla (çok çekirdekli sistemlerde)

### 2. Output Caching (İsteğe Bağlı)
Static içerik için output caching'i etkinleştirin

### 3. Compression
Static dosyalar için compression'ı etkinleştirin (IIS'de zaten varsayılan olarak açık)

## Güvenlik Kontrol Listesi

- [ ] DEBUG=False olarak ayarlandı
- [ ] SECRET_KEY güçlü ve güvenli
- [ ] ALLOWED_HOSTS doğru domain'lerle ayarlandı
- [ ] PostgreSQL güçlü şifre ile korunuyor
- [ ] .env dosyası git'e commit edilmedi
- [ ] HTTPS yapılandırıldı
- [ ] Gereksiz dosya izinleri kaldırıldı
- [ ] Log dosyaları için rotation ayarlandı
- [ ] Firewall kuralları yapılandırıldı
- [ ] PostgreSQL sadece localhost'tan erişilebilir
- [ ] Regular backup planı oluşturuldu

## Bakım ve İzleme

### Log Rotation
Windows Task Scheduler ile log dosyalarını düzenli olarak temizleyin

### Backup
Düzenli olarak PostgreSQL veritabanı ve media dosyalarını yedekleyin:

```powershell
# PostgreSQL Backup
pg_dump -U warandser_user -h localhost warandser_db > backup_%date:~10,4%%date:~4,2%%date:~7,2%.sql

# Media Backup
robocopy C:\inetpub\wwwroot\warandser\media C:\Backups\media /MIR /LOG:backup.log
```

### İzleme
- IIS log dosyalarını düzenli kontrol edin
- Django log dosyalarını izleyin
- PostgreSQL performansını takip edin

## Sorun Giderme

### "HTTP Error 500.0 - Internal Server Error"
- Python yolunu kontrol edin
- wfastcgi yolunu kontrol edin
- DJANGO_SETTINGS_MODULE'ü kontrol edin
- Log dosyalarını kontrol edin

### Static Dosyalar Yüklenmiyor
- `collectstatic` komutunu çalıştırdığınızdan emin olun
- Virtual directory'lerin doğru yapılandırıldığını kontrol edin
- Handler Mappings'te static dosyalar için istisna olduğundan emin olun

### Database Connection Error
- PostgreSQL'in çalıştığını kontrol edin
- `.env` dosyasındaki veritabanı bilgilerini kontrol edin
- PostgreSQL'in bağlantıya izin verdiğini kontrol edin (pg_hba.conf)

## Ek Kaynaklar

- Django Deployment Checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
- IIS Configuration Reference: https://docs.microsoft.com/en-us/iis/configuration/
- PostgreSQL Documentation: https://www.postgresql.org/docs/

## Destek

Sorun yaşarsanız:
1. Log dosyalarını kontrol edin
2. Django DEBUG=True yaparak detaylı hata mesajlarını görün
3. Event Viewer'ı kontrol edin
4. IIS log dosyalarını inceleyin

---

**Not:** Bu rehber, C:\Konnektom\WarAndSer yolu için hazırlanmıştır. Farklı bir yol kullanıyorsanız, tüm yolları buna göre güncelleyin.
