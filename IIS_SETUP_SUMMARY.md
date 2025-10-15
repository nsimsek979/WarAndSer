# IIS Production Setup - Kurulum Özeti

## ✅ Yapılan Değişiklikler

Bu proje artık **IIS (Internet Information Services)** üzerinde **PostgreSQL** veritabanı ile production ortamında çalışacak şekilde yapılandırılmıştır.

---

## 📦 Yeni Eklenen Dosyalar

### 1. Ayar Dosyaları
- **`gvs/settings_iis_prod.py`** - IIS için özel production ayarları
- **`web.config`** - IIS yapılandırma dosyası

### 2. Deployment Scriptleri
- **`deployment/iis_setup.ps1`** - Ana kurulum scripti
- **`deployment/iis_restart.ps1`** - Site yeniden başlatma
- **`deployment/collect_static.ps1`** - Static dosya toplama
- **`deployment/postgres_backup.ps1`** - PostgreSQL yedekleme
- **`deployment/setup_scheduled_backup.ps1`** - Otomatik yedekleme kurulumu
- **`deployment/iis_health_check.ps1`** - Sistem sağlık kontrolü
- **`deployment/env_template.txt`** - .env dosyası şablonu

### 3. Dokümantasyon
- **`IIS_DEPLOYMENT_GUIDE.md`** - Detaylı deployment rehberi (adım adım)
- **`IIS_PRODUCTION_README.md`** - Hızlı başlangıç rehberi
- **`deployment/QUICK_REFERENCE.md`** - Hızlı referans kartı
- **`IIS_SETUP_SUMMARY.md`** - Bu dosya (özet)

---

## 🔧 Güncellenen Dosyalar

### 1. requirements.txt
- **`wfastcgi==3.0.0`** eklendi (IIS FastCGI desteği için)

---

## 🎯 Özellikler

### IIS Desteği
- ✅ FastCGI üzerinden Django çalıştırma
- ✅ URL Rewrite kuralları
- ✅ Static ve Media dosya yönetimi
- ✅ Virtual Directory yapılandırması

### PostgreSQL Desteği
- ✅ PostgreSQL veritabanı yapılandırması
- ✅ Ortam değişkenleri ile bağlantı bilgileri
- ✅ UTF-8 encoding desteği

### Güvenlik
- ✅ Production security ayarları
- ✅ HTTPS desteği (opsiyonel)
- ✅ CSRF ve XSS koruması
- ✅ Güvenli session yönetimi

### Yedekleme ve İzleme
- ✅ Otomatik PostgreSQL yedekleme
- ✅ Log dosyası yönetimi
- ✅ Sistem sağlık kontrolü
- ✅ Hata izleme

---

## 📋 Kurulum Adımları (Özet)

### 1. Hızlı Kurulum
```powershell
# 1. Proje dizinine gidin
cd C:\Konnektom\WarAndSer

# 2. .env dosyası oluşturun
copy deployment\env_template.txt .env
notepad .env  # Değerleri güncelleyin

# 3. Sanal ortam oluşturun
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. PostgreSQL kurulumu ve veritabanı oluşturma
# (PostgreSQL kurulu olmalı)

# 5. Otomatik kurulum (Yönetici yetkisi gerekli)
.\deployment\iis_setup.ps1

# 6. IIS'de site oluşturun (Manuel - IIS Manager)
# Detaylar için: IIS_DEPLOYMENT_GUIDE.md
```

### 2. IIS Yapılandırması
- IIS Manager'da site oluşturma
- Handler Mappings ayarlama
- Virtual Directories (static, media) ekleme
- Detaylı adımlar için: **IIS_DEPLOYMENT_GUIDE.md**

---

## 📁 Proje Yapısı

```
WarAndSer/
│
├── deployment/                      # Deployment araçları
│   ├── iis_setup.ps1               # Ana kurulum
│   ├── iis_restart.ps1             # Site restart
│   ├── collect_static.ps1          # Static toplama
│   ├── postgres_backup.ps1         # Yedekleme
│   ├── setup_scheduled_backup.ps1  # Oto yedekleme
│   ├── iis_health_check.ps1        # Sağlık kontrolü
│   ├── env_template.txt            # .env şablonu
│   └── QUICK_REFERENCE.md          # Hızlı referans
│
├── gvs/
│   ├── settings_base.py            # Temel ayarlar
│   ├── settings_dev.py             # Development ayarları
│   ├── settings_prod.py            # Ubuntu production (mevcut)
│   ├── settings_iis_prod.py        # ⭐ IIS production (YENİ)
│   └── wsgi.py                     # WSGI yapılandırması
│
├── static/                         # Static dosyalar (dev)
├── staticfiles/                    # Collected static (gitignore)
├── media/                          # Media dosyalar (gitignore)
│
├── web.config                      # ⭐ IIS yapılandırması (YENİ)
├── .env                            # ⭐ Ortam değişkenleri (oluşturun!)
├── requirements.txt                # Python bağımlılıkları (güncellendi)
│
├── IIS_DEPLOYMENT_GUIDE.md         # ⭐ Detaylı rehber (YENİ)
├── IIS_PRODUCTION_README.md        # ⭐ Hızlı başlangıç (YENİ)
└── IIS_SETUP_SUMMARY.md            # ⭐ Bu dosya (YENİ)
```

---

## 🔐 Önemli Güvenlik Notları

### 1. .env Dosyası
```bash
# .env dosyası zaten .gitignore'da
# Asla Git'e commit etmeyin!
```

**Kritik Değişkenler:**
- `SECRET_KEY` - Django secret key (güçlü, benzersiz)
- `DB_PASSWORD` - PostgreSQL şifresi
- `DEBUG=False` - Production'da mutlaka False
- `ALLOWED_HOSTS` - Sadece geçerli domain'ler

### 2. Dosya İzinleri
```powershell
# IIS kullanıcılarına (IIS_IUSRS, IUSR) izinler:
# - Media klasörü: Yazma izni
# - Logs klasörü: Yazma izni
# - Proje klasörü: Okuma izni
```

### 3. PostgreSQL
- Güçlü şifre kullanın
- Sadece localhost'tan bağlantıya izin verin
- `pg_hba.conf` yapılandırmasını kontrol edin

---

## 🚀 İlk Deployment Checklist

### Ön Hazırlık
- [ ] Windows Server hazır
- [ ] IIS kurulu ve çalışıyor
- [ ] Python 3.10+ kurulu
- [ ] PostgreSQL kurulu

### Kurulum
- [ ] Proje klonlandı/kopyalandı
- [ ] Sanal ortam oluşturuldu
- [ ] Bağımlılıklar yüklendi
- [ ] `.env` dosyası oluşturuldu ve düzenlendi
- [ ] PostgreSQL veritabanı oluşturuldu
- [ ] `iis_setup.ps1` çalıştırıldı

### IIS Yapılandırması
- [ ] IIS'de site oluşturuldu
- [ ] Handler Mappings ayarlandı
- [ ] Virtual Directories (static, media) eklendi
- [ ] FastCGI settings yapılandırıldı
- [ ] Site başlatıldı

### Django Yapılandırması
- [ ] Migration'lar çalıştırıldı
- [ ] Static dosyalar toplandı
- [ ] Superuser oluşturuldu
- [ ] Admin paneline erişim test edildi

### Test
- [ ] Ana sayfa açılıyor
- [ ] Admin panel çalışıyor
- [ ] Static dosyalar yükleniyor
- [ ] Database bağlantısı çalışıyor
- [ ] Log dosyaları oluşuyor

### Güvenlik
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` güçlü ve benzersiz
- [ ] `ALLOWED_HOSTS` doğru
- [ ] HTTPS yapılandırıldı (production için)
- [ ] Firewall kuralları ayarlandı

### Backup
- [ ] Manuel backup testi yapıldı
- [ ] Otomatik backup kuruldu
- [ ] Backup restore testi yapıldı

---

## 📚 Hangi Dökümanı Kullanmalıyım?

### Yeni Kurulum Yapıyorsanız
1. **Başlangıç:** `IIS_PRODUCTION_README.md` (hızlı genel bakış)
2. **Detaylı Kurulum:** `IIS_DEPLOYMENT_GUIDE.md` (adım adım rehber)
3. **Her Zaman Yanınızda:** `deployment/QUICK_REFERENCE.md` (yazdırın!)

### Mevcut Sistem İçin
- **Günlük İşler:** `deployment/QUICK_REFERENCE.md`
- **Sorun Giderme:** `IIS_DEPLOYMENT_GUIDE.md` → "Sorun Giderme" bölümü
- **Yeni Feature Deploy:** `deployment/QUICK_REFERENCE.md` → "Deployment İş Akışı"

### Geliştirme Ortamında
- Mevcut `settings_dev.py` kullanın
- Development ortamı değişmedi

---

## 🛠️ Yaygın Komutlar

### Site Yönetimi
```powershell
# Site'ı yeniden başlat
.\deployment\iis_restart.ps1

# Static dosyaları topla
.\deployment\collect_static.ps1

# Sistem sağlık kontrolü
.\deployment\iis_health_check.ps1
```

### Veritabanı
```powershell
# Backup al
.\deployment\postgres_backup.ps1

# Migration çalıştır
.\venv\Scripts\activate
$env:DJANGO_SETTINGS_MODULE="gvs.settings_iis_prod"
python manage.py migrate
```

### Log İzleme
```powershell
# Hata logları
Get-Content C:\inetpub\wwwroot\warandser\logs\django_error.log -Tail 50 -Wait
```

---

## 🔄 Kod Güncelleme İş Akışı

Her kod güncellemesinden sonra:

```powershell
# 1. Kodu çek
git pull origin main

# 2. Bağımlılıkları güncelle
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. Migration çalıştır
$env:DJANGO_SETTINGS_MODULE="gvs.settings_iis_prod"
python manage.py migrate

# 4. Static topla
deactivate
.\deployment\collect_static.ps1

# 5. Site'ı restart et
.\deployment\iis_restart.ps1

# 6. Kontrol et
.\deployment\iis_health_check.ps1
```

---

## 🆘 Yardım ve Destek

### Sorun Yaşıyorsanız

1. **Log Dosyalarını Kontrol Edin:**
   - `C:\inetpub\wwwroot\warandser\logs\django_error.log`
   - `C:\inetpub\logs\LogFiles` (IIS logs)

2. **Sağlık Kontrolü Çalıştırın:**
   ```powershell
   .\deployment\iis_health_check.ps1
   ```

3. **Event Viewer'ı Kontrol Edin:**
   ```
   eventvwr.msc
   ```

4. **Detaylı Sorun Giderme:**
   `IIS_DEPLOYMENT_GUIDE.md` → "Sorun Giderme" bölümü

---

## 📞 İletişim ve Kaynaklar

### Dökümanlar
- **IIS_DEPLOYMENT_GUIDE.md** - Kapsamlı deployment rehberi
- **IIS_PRODUCTION_README.md** - Hızlı başlangıç
- **deployment/QUICK_REFERENCE.md** - Komut referansı

### Dış Kaynaklar
- Django Docs: https://docs.djangoproject.com/
- IIS Docs: https://docs.microsoft.com/iis/
- PostgreSQL Docs: https://www.postgresql.org/docs/
- wfastcgi: https://pypi.org/project/wfastcgi/

---

## ✨ Önemli Notlar

### 1. Ortam Farkları
- **Development (Windows):** `settings_dev.py` - SQLite
- **Production (Ubuntu):** `settings_prod.py` - PostgreSQL/MySQL
- **Production (IIS/Windows):** `settings_iis_prod.py` - PostgreSQL ⭐

### 2. Settings Seçimi
Django otomatik olarak doğru settings'i yükler:
- Windows: `settings_dev.py` (development)
- Linux/Ubuntu: `settings_prod.py` (production)
- IIS: `DJANGO_SETTINGS_MODULE` environment variable ile `settings_iis_prod.py`

### 3. Celery (Opsiyonel)
Windows'ta Celery kullanmak isterseniz:
- Redis kurulumu gerekli
- Celery worker'ı gevent/solo pool ile çalıştırın
- Alternatif: Windows Task Scheduler (zaten mevcut scriptler var)

### 4. HTTPS
Production ortamında mutlaka HTTPS kullanın:
- SSL sertifikası edinin (Let's Encrypt önerilir)
- IIS'de HTTPS binding ekleyin
- `.env` dosyasında `USE_HTTPS=True` yapın

---

## 🎉 Sonuç

Projeniz artık IIS üzerinde PostgreSQL ile production ortamında çalışmaya hazır!

**Başarılar! 🚀**

---

**Son Güncelleme:** 2025-10-11
**Versiyon:** 1.0.0
