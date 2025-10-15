# IIS Production Deployment - Hızlı Başlangıç

Bu proje artık IIS üzerinde PostgreSQL ile production ortamında çalışacak şekilde yapılandırılmıştır.

## 📋 Gereksinimler

- Windows Server 2016+ veya Windows 10/11
- IIS 8.0+
- Python 3.10+
- PostgreSQL 14+
- .NET Framework (IIS için)

## 🚀 Hızlı Kurulum

### 1. Ortam Hazırlığı

```powershell
# Proje dizinine gidin
cd C:\Konnektom\WarAndSer

# Sanal ortam oluşturun
python -m venv venv
.\venv\Scripts\Activate.ps1

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 2. PostgreSQL Kurulumu

PostgreSQL'i indirin ve kurun, ardından veritabanını oluşturun:

```sql
CREATE DATABASE warandser_db;
CREATE USER warandser_user WITH PASSWORD 'Konnektom123*';
GRANT ALL PRIVILEGES ON DATABASE warandser_db TO warandser_user;
```

### 3. Ortam Değişkenleri (.env)

Proje kök dizininde `.env` dosyası oluşturun:

```powershell
# Template'i kopyalayın
copy deployment\env_template.txt .env

# .env dosyasını düzenleyin ve gerçek değerlerinizi girin
notepad .env
```

**Önemli değişkenler:**
- `SECRET_KEY`: Güçlü, rastgele bir anahtar
- `DB_PASSWORD`: PostgreSQL şifreniz
- `ALLOWED_HOSTS`: Domain adınız
- `EMAIL_*`: Email ayarlarınız

### 4. Otomatik Kurulum

Yönetici yetkisi ile PowerShell açın ve çalıştırın:

```powershell
cd C:\Konnektom\WarAndSer
.\deployment\iis_setup.ps1
```

Bu script:
- ✅ Gerekli klasörleri oluşturur
- ✅ IIS izinlerini ayarlar
- ✅ wfastcgi'yi etkinleştirir
- ✅ Migration'ları çalıştırır
- ✅ Static dosyaları toplar

### 5. IIS Yapılandırması

**Manuel adımlar:**

1. **IIS Manager'ı açın** (`inetmgr`)

2. **Site oluşturun:**
   - Sol panelde "Sites" → Sağ tık → "Add Website"
   - Site name: `WarAndSer`
   - Physical path: `C:\Konnektom\WarAndSer`
   - Port: `80`

3. **Handler Mapping ekleyin:**
   - Site'ı seçin → "Handler Mappings" → "Add Module Mapping"
   - Request path: `*`
   - Module: `FastCgiModule`
   - Executable: `C:\Python312\python.exe|C:\Python312\Lib\site-packages\wfastcgi.py`
   - Name: `Python FastCGI`

4. **Virtual Directories oluşturun:**
   - **static:** `C:\inetpub\wwwroot\warandser\static`
   - **media:** `C:\inetpub\wwwroot\warandser\media`

5. **Site'ı başlatın**

Detaylı rehber için: **`IIS_DEPLOYMENT_GUIDE.md`**

## 📁 Dosya Yapısı

```
WarAndSer/
├── deployment/
│   ├── iis_setup.ps1              # Ana kurulum scripti
│   ├── iis_restart.ps1            # Site yeniden başlatma
│   ├── collect_static.ps1         # Static dosya toplama
│   ├── postgres_backup.ps1        # Veritabanı yedekleme
│   ├── setup_scheduled_backup.ps1 # Otomatik yedekleme
│   └── env_template.txt           # .env şablonu
├── gvs/
│   ├── settings_iis_prod.py       # IIS production ayarları
│   └── settings.py                # Ana settings dosyası
├── web.config                     # IIS yapılandırma dosyası
└── .env                           # Ortam değişkenleri (oluşturun!)
```

## 🔧 Yardımcı Scriptler

### Site Yeniden Başlatma
```powershell
.\deployment\iis_restart.ps1
```

### Static Dosyaları Toplama
```powershell
.\deployment\collect_static.ps1
```

### Manuel Migration
```powershell
.\venv\Scripts\activate
$env:DJANGO_SETTINGS_MODULE="gvs.settings_iis_prod"
python manage.py migrate
```

### Superuser Oluşturma
```powershell
.\venv\Scripts\activate
$env:DJANGO_SETTINGS_MODULE="gvs.settings_iis_prod"
python manage.py createsuperuser
```

## 💾 Yedekleme

### Manuel Yedekleme
```powershell
.\deployment\postgres_backup.ps1
```

### Otomatik Yedekleme (Günlük)
```powershell
.\deployment\setup_scheduled_backup.ps1
```

Her gün saat 02:00'de otomatik yedekleme yapılır.

## 📊 Loglama

Log dosyaları:
- Django: `C:\inetpub\wwwroot\warandser\logs\django_error.log`
- Django Info: `C:\inetpub\wwwroot\warandser\logs\django_info.log`
- wfastcgi: `C:\Konnektom\WarAndSer\logs\wfastcgi.log`
- IIS: `C:\inetpub\logs\LogFiles`

## 🐛 Sorun Giderme

### "HTTP Error 500.0"
```powershell
# Log dosyalarını kontrol edin
type C:\inetpub\wwwroot\warandser\logs\django_error.log
```

### Static Dosyalar Yüklenmiyor
```powershell
# Static dosyaları yeniden toplayın
.\deployment\collect_static.ps1

# IIS'i yeniden başlatın
.\deployment\iis_restart.ps1
```

### Database Connection Error
```powershell
# PostgreSQL servisini kontrol edin
Get-Service -Name "postgresql*"

# .env dosyasını kontrol edin
notepad .env
```

### Migration Hatası
```powershell
# Migration'ları sıfırlayın (dikkatli!)
.\venv\Scripts\activate
$env:DJANGO_SETTINGS_MODULE="gvs.settings_iis_prod"
python manage.py showmigrations
```

## 🔒 Güvenlik Kontrol Listesi

- [ ] `DEBUG=False` (.env)
- [ ] `SECRET_KEY` güçlü ve benzersiz
- [ ] `ALLOWED_HOSTS` sadece domain'leri içeriyor
- [ ] PostgreSQL güçlü şifre
- [ ] `.env` dosyası `.gitignore`'da
- [ ] HTTPS yapılandırıldı (production için)
- [ ] Firewall kuralları ayarlandı
- [ ] Regular backup planı aktif
- [ ] Log rotation ayarlandı

## 📝 Deployment Checklist

**İlk Deployment:**
- [ ] PostgreSQL kuruldu ve veritabanı oluşturuldu
- [ ] `.env` dosyası oluşturuldu ve yapılandırıldı
- [ ] Sanal ortam oluşturuldu
- [ ] Bağımlılıklar yüklendi
- [ ] `iis_setup.ps1` çalıştırıldı
- [ ] IIS'de site oluşturuldu
- [ ] Handler mappings yapılandırıldı
- [ ] Virtual directories eklendi
- [ ] Site başlatıldı ve test edildi
- [ ] Superuser oluşturuldu
- [ ] Backup planı ayarlandı

**Her Update'te:**
- [ ] Kod güncellemeleri çekildi (`git pull`)
- [ ] Yeni bağımlılıklar yüklendi (`pip install -r requirements.txt`)
- [ ] Migration'lar çalıştırıldı (`python manage.py migrate`)
- [ ] Static dosyalar toplandı (`.\deployment\collect_static.ps1`)
- [ ] Site yeniden başlatıldı (`.\deployment\iis_restart.ps1`)

## 🌐 Test Etme

1. **Ana sayfa:**
   ```
   http://localhost
   ```

2. **Admin panel:**
   ```
   http://localhost/admin
   ```

3. **API (varsa):**
   ```
   http://localhost/api/
   ```

## 📞 Destek

Sorun yaşarsanız:
1. Log dosyalarını kontrol edin
2. `IIS_DEPLOYMENT_GUIDE.md` dosyasına bakın
3. Event Viewer'ı kontrol edin (eventvwr.msc)
4. IIS'i yeniden başlatın

## 📚 Ek Kaynaklar

- **Detaylı Rehber:** `IIS_DEPLOYMENT_GUIDE.md`
- **Django Docs:** https://docs.djangoproject.com/
- **IIS Docs:** https://docs.microsoft.com/iis/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/

---

**Not:** Bu dokümantasyon Windows Server ortamı için hazırlanmıştır. Ubuntu/Linux deployment için `DEPLOYMENT_README.md` dosyasına bakın.
