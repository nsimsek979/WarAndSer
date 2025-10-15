# IIS Django - Hızlı Referans Kartı

## 🚀 Yaygın Komutlar

### Site Yönetimi
```powershell
# Site'ı yeniden başlat
.\deployment\iis_restart.ps1

# Static dosyaları topla
.\deployment\collect_static.ps1

# Manuel migration
.\venv\Scripts\activate
$env:DJANGO_SETTINGS_MODULE="gvs.settings_iis_prod"
python manage.py migrate
```

### Veritabanı
```powershell
# Backup al
.\deployment\postgres_backup.ps1

# Migration durumunu kontrol et
python manage.py showmigrations

# Yeni migration oluştur
python manage.py makemigrations

# Superuser oluştur
python manage.py createsuperuser
```

### Log İzleme
```powershell
# Django error log
Get-Content C:\inetpub\wwwroot\warandser\logs\django_error.log -Tail 50 -Wait

# Django info log
Get-Content C:\inetpub\wwwroot\warandser\logs\django_info.log -Tail 50 -Wait

# IIS log
Get-Content "C:\inetpub\logs\LogFiles\W3SVC*\*.log" | Select-Object -Last 50
```

### IIS Servis Yönetimi
```powershell
# IIS'i yeniden başlat
iisreset

# Application Pool'u durdur/başlat
Import-Module WebAdministration
Stop-WebAppPool -Name "DefaultAppPool"
Start-WebAppPool -Name "DefaultAppPool"

# Site'ı durdur/başlat
Stop-Website -Name "WarAndSer"
Start-Website -Name "WarAndSer"
```

### PostgreSQL
```powershell
# Servis kontrolü
Get-Service -Name "postgresql*"

# Servis başlat/durdur
Start-Service -Name "postgresql-x64-14"
Stop-Service -Name "postgresql-x64-14"

# psql bağlantısı
psql -U postgres -d warandser_db
```

## 📁 Önemli Dosya Konumları

### Proje Dosyaları
- **Proje:** `C:\Konnektom\WarAndSer`
- **Settings:** `C:\Konnektom\WarAndSer\gvs\settings_iis_prod.py`
- **web.config:** `C:\Konnektom\WarAndSer\web.config`
- **.env:** `C:\Konnektom\WarAndSer\.env`

### Static/Media
- **Static:** `C:\inetpub\wwwroot\warandser\static`
- **Media:** `C:\inetpub\wwwroot\warandser\media`

### Logs
- **Django Error:** `C:\inetpub\wwwroot\warandser\logs\django_error.log`
- **Django Info:** `C:\inetpub\wwwroot\warandser\logs\django_info.log`
- **IIS Logs:** `C:\inetpub\logs\LogFiles`
- **wfastcgi:** `C:\Konnektom\WarAndSer\logs\wfastcgi.log`

### Backup
- **Default Location:** `C:\Backups\PostgreSQL`

## 🔧 Sorun Giderme

### 500 Internal Server Error
1. Log dosyalarını kontrol et
2. DEBUG=True yap (geçici)
3. Event Viewer kontrol et
4. IIS'i yeniden başlat

### Static Dosyalar Yüklenmiyor
```powershell
.\deployment\collect_static.ps1
.\deployment\iis_restart.ps1
```

### Database Bağlantı Hatası
1. PostgreSQL servisini kontrol et
2. `.env` dosyasını kontrol et
3. pg_hba.conf'u kontrol et (localhost'a izin var mı?)

### Module Import Hatası
```powershell
# Bağımlılıkları yeniden yükle
.\venv\Scripts\activate
pip install -r requirements.txt --force-reinstall
```

## 🔄 Deployment İş Akışı

### Kod Güncellemesi Sonrası
```powershell
# 1. Kodu çek
git pull origin main

# 2. Sanal ortamı aktifleştir
.\venv\Scripts\activate

# 3. Bağımlılıkları güncelle
pip install -r requirements.txt

# 4. Migration çalıştır
$env:DJANGO_SETTINGS_MODULE="gvs.settings_iis_prod"
python manage.py migrate

# 5. Static dosyaları topla
deactivate
.\deployment\collect_static.ps1

# 6. Site'ı yeniden başlat
.\deployment\iis_restart.ps1

# 7. Log kontrol et
Get-Content C:\inetpub\wwwroot\warandser\logs\django_error.log -Tail 20
```

### Yeni Feature Deploy
```powershell
# 1. Backup al
.\deployment\postgres_backup.ps1

# 2. Kod güncellemesi iş akışını takip et (yukarıdaki)

# 3. Test et
Start-Process "http://localhost"
Start-Process "http://localhost/admin"
```

## 🔒 Güvenlik Kontrolü

### Hızlı Güvenlik Check
```powershell
# .env dosyasını kontrol et
Select-String -Path .env -Pattern "SECRET_KEY|DEBUG|DB_PASSWORD"

# ALLOWED_HOSTS kontrol
Select-String -Path gvs/settings_iis_prod.py -Pattern "ALLOWED_HOSTS"

# Log izinlerini kontrol
icacls "C:\inetpub\wwwroot\warandser\logs"
```

## 📊 Monitoring

### CPU/Memory İzleme
```powershell
# IIS Worker Process
Get-Process -Name "w3wp" | Select-Object CPU,WorkingSet,Id

# Python Process
Get-Process -Name "python" | Select-Object CPU,WorkingSet,Id
```

### Disk Kullanımı
```powershell
# Media klasörü boyutu
(Get-ChildItem C:\inetpub\wwwroot\warandser\media -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB

# Log klasörü boyutu
(Get-ChildItem C:\inetpub\wwwroot\warandser\logs -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
```

### Database Boyutu
```sql
-- psql'de çalıştır
SELECT pg_size_pretty(pg_database_size('warandser_db'));
```

## 🔄 Bakım Görevleri

### Günlük
- [ ] Log dosyalarını kontrol et
- [ ] Hata sayısını gözden geçir
- [ ] Disk alanını kontrol et

### Haftalık
- [ ] Backup'ları kontrol et
- [ ] Performance metrics'i gözden geçir
- [ ] Güvenlik loglarını incele

### Aylık
- [ ] Eski log dosyalarını temizle
- [ ] Media klasörünü gözden geçir
- [ ] Dependency güncellemelerini kontrol et
- [ ] SSL sertifikası kontrolü

## 📱 Hızlı Test

```powershell
# Site erişim testi
Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing

# Admin panel testi
Invoke-WebRequest -Uri "http://localhost/admin" -UseBasicParsing

# Static dosya testi
Invoke-WebRequest -Uri "http://localhost/static/css/styles.css" -UseBasicParsing

# API testi (varsa)
Invoke-WebRequest -Uri "http://localhost/api/" -UseBasicParsing
```

## 🎯 Performance Tuning

### Application Pool Settings
```
- Start Mode: AlwaysRunning
- Idle Time-out: 0
- Max Worker Processes: 2-4
- Regular Time Interval: 1740 (29 hours)
```

### PostgreSQL
```sql
-- Connection pooling
-- Optimize queries
-- Regular VACUUM ANALYZE
```

### Cache
Django cache framework'ü kullan:
- File-based cache (varsayılan)
- Redis cache (daha performanslı)

## 🆘 Acil Durum

### Site Çalışmıyorsa
```powershell
# 1. IIS'i yeniden başlat
iisreset

# 2. PostgreSQL'i kontrol et
Get-Service postgresql*

# 3. Hata loglarını kontrol et
Get-Content C:\inetpub\wwwroot\warandser\logs\django_error.log -Tail 50

# 4. Event Viewer'ı aç
eventvwr.msc
```

### Database Restore (Acil Durum)
```powershell
# En son backup'ı bul
Get-ChildItem C:\Backups\PostgreSQL -Filter "*.sql" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Restore et
psql -U postgres -d warandser_db -f "backup_file.sql"
```

## 📞 İletişim

### Sistem Bilgileri
```powershell
# OS Version
Get-ComputerInfo | Select-Object WindowsVersion, OsArchitecture

# IIS Version
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\InetStp\ | Select-Object VersionString

# Python Version
python --version

# PostgreSQL Version
psql --version
```

---

**Not:** Bu referans kartını yazdırıp masanızda bulundurabilirsiniz!
