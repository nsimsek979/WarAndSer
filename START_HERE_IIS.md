# 🚀 IIS Production - BURADAN BAŞLAYIN

## Hoş Geldiniz!

Bu proje artık **IIS** üzerinde **PostgreSQL** ile production ortamında çalışacak şekilde yapılandırılmıştır.

---

## ⚡ 3 Adımda Başlangıç

### 1️⃣ Hızlı Genel Bakış (5 dakika)
```
📄 IIS_PRODUCTION_README.md
```
Hızlı başlangıç rehberi - ne yapılacağına genel bakış

### 2️⃣ Detaylı Kurulum (30-60 dakika)
```
📄 IIS_DEPLOYMENT_GUIDE.md
```
Adım adım kurulum rehberi - her şey detaylıca anlatılmış

### 3️⃣ Günlük Kullanım
```
📄 deployment/QUICK_REFERENCE.md
```
Hızlı referans kartı - yazdırıp masanızda bulundurun!

---

## 📊 Durum Kontrolü

### Sisteminiz Hazır mı?

Aşağıdaki komutları çalıştırarak kontrol edin:

```powershell
# Python kontrolü
python --version
# Beklenen: Python 3.10 veya üzeri

# PostgreSQL kontrolü
Get-Service -Name "postgresql*"
# Beklenen: Running

# IIS kontrolü
Get-Service W3SVC
# Beklenen: Running
```

✅ **Hepsi hazır mı?** → Bir sonraki adıma geçin!
❌ **Eksik var mı?** → `IIS_DEPLOYMENT_GUIDE.md` → "Gereksinimler" bölümü

---

## 🎯 Hangi Durumdasınız?

### A) Yeni Kurulum Yapacağım
```
1. IIS_PRODUCTION_README.md (oku)
2. .env dosyası oluştur (deployment/env_template.txt'den)
3. PostgreSQL veritabanı oluştur
4. deployment/iis_setup.ps1 (çalıştır)
5. IIS'de site oluştur (IIS_DEPLOYMENT_GUIDE.md)
6. Test et!
```

### B) Var Olan Sistemi Güncelliyorum
```powershell
# Hızlı güncelleme
git pull
.\venv\Scripts\activate
pip install -r requirements.txt
$env:DJANGO_SETTINGS_MODULE="gvs.settings_iis_prod"
python manage.py migrate
deactivate
.\deployment\collect_static.ps1
.\deployment\iis_restart.ps1
```

### C) Sorun Giderme Yapıyorum
```powershell
# Sistem sağlık kontrolü
.\deployment\iis_health_check.ps1

# Log kontrolü
Get-Content C:\inetpub\wwwroot\warandser\logs\django_error.log -Tail 50
```
Detaylı sorun giderme: `IIS_DEPLOYMENT_GUIDE.md` → "Sorun Giderme"

---

## 📁 Önemli Dosyalar

### Okumanız Gerekenler (Öncelik Sırasına Göre)

| Dosya | Açıklama | Ne Zaman? |
|-------|----------|-----------|
| `IIS_PRODUCTION_README.md` | Hızlı başlangıç | İLK ÖNCE oku |
| `IIS_DEPLOYMENT_GUIDE.md` | Detaylı rehber | Kurulum yaparken |
| `deployment/QUICK_REFERENCE.md` | Komut referansı | Her zaman yanında |
| `IIS_SETUP_SUMMARY.md` | Neler değişti? | Değişiklikleri görmek için |

### Kurulum Scriptleri

| Script | Açıklama | Kullanım |
|--------|----------|----------|
| `iis_setup.ps1` | Ana kurulum | İlk kurulumda 1 kez |
| `iis_restart.ps1` | Site restart | Her güncellemede |
| `collect_static.ps1` | Static topla | CSS/JS değişince |
| `iis_health_check.ps1` | Sağlık kontrolü | Düzenli kontrol |
| `postgres_backup.ps1` | Yedek al | Günlük/İstek üzerine |

---

## ⚙️ İlk Kurulum (Özetle)

### Adım 1: Ortam Hazırlığı
```powershell
cd C:\Konnektom\WarAndSer

# Sanal ortam
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Adım 2: Yapılandırma
```powershell
# .env oluştur
copy deployment\env_template.txt .env
notepad .env  # Düzenle!
```

**Mutlaka ayarlanması gerekenler:**
- `SECRET_KEY` (güçlü, rastgele)
- `DB_PASSWORD` (PostgreSQL şifresi)
- `ALLOWED_HOSTS` (domain adı)

### Adım 3: Veritabanı
```sql
-- PostgreSQL'de çalıştır (pgAdmin veya psql)
CREATE DATABASE warandser_db;
CREATE USER warandser_user WITH PASSWORD 'güçlü_şifre';
GRANT ALL PRIVILEGES ON DATABASE warandser_db TO warandser_user;
```

### Adım 4: Otomatik Kurulum
```powershell
# YÖNETİCİ YETKİSİ İLE çalıştır
.\deployment\iis_setup.ps1
```

### Adım 5: IIS Yapılandırması
- IIS Manager'ı aç (`inetmgr`)
- Site oluştur (Detaylar: `IIS_DEPLOYMENT_GUIDE.md`)
- Handler Mappings ekle
- Virtual Directories ekle (static, media)
- Site'ı başlat

### Adım 6: Test
```powershell
# Sağlık kontrolü
.\deployment\iis_health_check.ps1

# Tarayıcıda aç
Start-Process "http://localhost"
Start-Process "http://localhost/admin"
```

---

## 🔐 GÜVENLİK UYARISI!

### ⚠️ Production'a almadan önce MUTLAKA kontrol edin:

- [ ] `.env` dosyası `.gitignore`'da (✓ zaten var)
- [ ] `DEBUG=False` (.env dosyasında)
- [ ] `SECRET_KEY` güçlü ve benzersiz
- [ ] `ALLOWED_HOSTS` sadece geçerli domain'leri içeriyor
- [ ] PostgreSQL güçlü şifre ile korunuyor
- [ ] HTTPS yapılandırıldı (production için şart!)
- [ ] Firewall kuralları ayarlandı
- [ ] Backup planı aktif

---

## 🆘 Acil Durum

### Site çalışmıyorsa:

```powershell
# 1. IIS'i restart et
iisreset

# 2. Sağlık kontrolü yap
.\deployment\iis_health_check.ps1

# 3. Log kontrol et
Get-Content C:\inetpub\wwwroot\warandser\logs\django_error.log -Tail 50

# 4. PostgreSQL kontrolü
Get-Service -Name "postgresql*"
```

### Hala çalışmıyorsa:
📖 `IIS_DEPLOYMENT_GUIDE.md` → "Sorun Giderme" bölümü

---

## 💡 Önemli Notlar

### .env Dosyası
- Template: `deployment/env_template.txt`
- **ASLA Git'e commit ETMEYİN** (zaten .gitignore'da)
- Her production ortamı için farklı değerler kullanın

### Settings Dosyaları
- **Development:** `settings_dev.py` (SQLite)
- **Production (Ubuntu):** `settings_prod.py`
- **Production (IIS):** `settings_iis_prod.py` ⭐ YENİ

### Logs
- **Django:** `C:\inetpub\wwwroot\warandser\logs\`
- **IIS:** `C:\inetpub\logs\LogFiles\`
- **Event Viewer:** `eventvwr.msc`

---

## 📞 Yardım

### Daha Fazla Bilgi

| Konu | Dosya |
|------|-------|
| Hızlı başlangıç | IIS_PRODUCTION_README.md |
| Detaylı rehber | IIS_DEPLOYMENT_GUIDE.md |
| Komut referansı | deployment/QUICK_REFERENCE.md |
| Değişiklikler | IIS_SETUP_SUMMARY.md |

### Dış Kaynaklar
- Django: https://docs.djangoproject.com/
- IIS: https://docs.microsoft.com/iis/
- PostgreSQL: https://www.postgresql.org/docs/

---

## ✅ Kurulum Tamamlandıysa

Tebrikler! 🎉

Artık şunları yapabilirsiniz:
- ✅ Site'i production'a alabilirsiniz
- ✅ Günlük operasyonlar için `deployment/QUICK_REFERENCE.md` kullanın
- ✅ `.\deployment\iis_health_check.ps1` ile düzenli kontrol yapın

---

## 🎯 Sonraki Adımlar

1. **İlk Deployment:**
   - Domain adını ayarlayın
   - SSL sertifikası edinin (Let's Encrypt)
   - HTTPS'i aktive edin
   - Firewall kurallarını yapılandırın

2. **Düzenli Bakım:**
   - Günlük log kontrolü
   - Haftalık backup kontrolü
   - Aylık güvenlik güncellemeleri

3. **Monitoring:**
   - `iis_health_check.ps1` scriptini otomatikleştirin
   - Email bildirimleri ayarlayın

---

**İyi Çalışmalar! 🚀**

*Bu dosya, IIS production setup'ı için başlangıç noktanızdır.*
*Detaylı bilgi için yukarıdaki dökümanları inceleyin.*

---

**Quick Links:**
- 📘 [IIS_PRODUCTION_README.md](IIS_PRODUCTION_README.md) - Başlangıç
- 📗 [IIS_DEPLOYMENT_GUIDE.md](IIS_DEPLOYMENT_GUIDE.md) - Detaylı Rehber
- 📙 [deployment/QUICK_REFERENCE.md](deployment/QUICK_REFERENCE.md) - Komutlar
