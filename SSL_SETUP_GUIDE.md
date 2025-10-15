# SSL Sertifikası Kurulum Rehberi - IIS

## 📋 Gereksinimler

Elinizde olması gerekenler:
- **domain.crt** (Sertifika dosyası)
- **domain.key** (Private key)
- **ca-bundle.crt** (Ara sertifikalar/Certificate Authority bundle)

---

## 🔧 Adım 1: PFX Dosyası Oluşturma

IIS, PFX (PKCS#12) formatında sertifika gerektirir.

### OpenSSL ile Birleştirme

```powershell
# OpenSSL kurulu değilse indirin:
# https://slproweb.com/products/Win32OpenSSL.html

# Sertifikaları birleştirin
openssl pkcs12 -export -out certificate.pfx `
  -inkey domain.key `
  -in domain.crt `
  -certfile ca-bundle.crt `
  -password pass:GüçlüŞifre123

# Dosya oluşturuldu: certificate.pfx
```

**Alternatif:** Online araçlar kullanabilirsiniz (güvenlik riski!)

---

## 🚀 Adım 2: Otomatik Kurulum (Önerilen)

```powershell
# Yönetici yetkisi ile PowerShell
cd C:\Konnektom\WarAndSer
.\deployment\iis_ssl_setup.ps1
```

Script şunları yapar:
1. PFX dosyasını import eder
2. IIS'de HTTPS binding oluşturur
3. Sertifikayı binding'e atar

---

## 📝 Adım 3: Manuel Kurulum

### 1. Sertifikayı Import Etme

```powershell
# PowerShell (Yönetici)
$pfxPassword = ConvertTo-SecureString -String "GüçlüŞifre123" -AsPlainText -Force
Import-PfxCertificate -FilePath "C:\path\to\certificate.pfx" `
    -CertStoreLocation Cert:\LocalMachine\My `
    -Password $pfxPassword
```

**VEYA GUI ile:**

1. `Win + R` → `mmc`
2. File → Add/Remove Snap-in
3. Certificates → Add → Computer account → Local computer
4. Certificates (Local Computer) → Personal → Certificates
5. Sağ tık → All Tasks → Import
6. PFX dosyasını seçin ve şifreyi girin

### 2. IIS'de HTTPS Binding Ekleme

1. **IIS Manager'ı açın** (`inetmgr`)

2. Sol panelde **WarAndSer** site'ını seçin

3. Sağ tarafta **Bindings...** tıklayın

4. **Add** butonuna tıklayın

5. Ayarları yapın:
   - **Type:** `https`
   - **IP address:** `All Unassigned`
   - **Port:** `443`
   - **Host name:** `yourdomain.com` (opsiyonel)
   - **SSL certificate:** Dropdown'dan sertifikanızı seçin

6. **OK** → **Close**

---

## 🔐 Adım 4: Django Ayarları

### .env Dosyasını Güncelleyin

```env
# .env dosyası
USE_HTTPS=True
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Site'ı Yeniden Başlatın

```powershell
.\deployment\iis_restart.ps1
```

---

## ✅ Adım 5: Test Etme

### Browser Test
```
https://yourdomain.com
https://yourdomain.com/admin
```

### PowerShell Test
```powershell
# SSL bağlantısını test et
Invoke-WebRequest -Uri "https://yourdomain.com" -UseBasicParsing

# Sertifika bilgilerini görüntüle
$url = "https://yourdomain.com"
$request = [System.Net.WebRequest]::Create($url)
$request.GetResponse() | Out-Null
$cert = $request.ServicePoint.Certificate
$cert | Format-List *
```

### Online Araçlar
- **SSL Labs:** https://www.ssllabs.com/ssltest/
- **SSL Checker:** https://www.sslshopper.com/ssl-checker.html

---

## 🔄 HTTP'den HTTPS'e Yönlendirme

### web.config'e Ekleyin

`web.config` dosyasındaki `<rewrite>` bölümüne ekleyin:

```xml
<rewrite>
  <rules>
    <!-- HTTP to HTTPS redirect -->
    <rule name="HTTP to HTTPS redirect" stopProcessing="true">
      <match url="(.*)" />
      <conditions>
        <add input="{HTTPS}" pattern="off" ignoreCase="true" />
      </conditions>
      <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" redirectType="Permanent" />
    </rule>

    <!-- Mevcut kurallar buradan devam eder -->
    <!-- ... -->
  </rules>
</rewrite>
```

---

## 🛠️ Sorun Giderme

### "Certificate not found" Hatası

```powershell
# Sertifikaları listele
Get-ChildItem -Path Cert:\LocalMachine\My

# Doğru store'da olduğundan emin olun
# Personal (My) store'da olmalı
```

### "The specified network password is not correct"

```powershell
# PFX şifresini doğru girdiğinizden emin olun
# Şifresiz PFX oluşturmak için:
openssl pkcs12 -export -out certificate.pfx `
  -inkey domain.key `
  -in domain.crt `
  -certfile ca-bundle.crt `
  -passout pass:
```

### Sertifika Süre Dolmuş

```powershell
# Sertifika tarihlerini kontrol et
$cert = Get-ChildItem -Path Cert:\LocalMachine\My | Where-Object {$_.Subject -like "*yourdomain*"}
Write-Host "Not Before: $($cert.NotBefore)"
Write-Host "Not After: $($cert.NotAfter)"
```

### Mixed Content Warning (HTTP/HTTPS karışık içerik)

```python
# settings_iis_prod.py
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 🔄 Sertifika Yenileme

### Let's Encrypt Oto-Yenileme (Önerilen)

```powershell
# Certify The Web aracını kullanın (ücretsiz)
# https://certifytheweb.com/

# VEYA win-acme
# https://www.win-acme.com/
```

### Manuel Yenileme

1. Yeni PFX dosyası oluşturun
2. Eski sertifikayı kaldırın
3. Yeni sertifikayı import edin
4. IIS binding'i güncelleyin

```powershell
# Eski sertifikayı kaldır
$oldCert = Get-ChildItem -Path Cert:\LocalMachine\My |
    Where-Object {$_.Thumbprint -eq "EskiThumbprint"}
Remove-Item -Path $oldCert.PSPath

# Yeni sertifikayı import et
$newCert = Import-PfxCertificate -FilePath "new-certificate.pfx" `
    -CertStoreLocation Cert:\LocalMachine\My `
    -Password $pfxPassword

# Binding'i güncelle
$binding = Get-WebBinding -Name "WarAndSer" -Protocol "https"
$binding.AddSslCertificate($newCert.Thumbprint, "my")
```

---

## 📞 Ek Kaynaklar

- **IIS SSL Docs:** https://docs.microsoft.com/en-us/iis/manage/configuring-security/how-to-set-up-ssl-on-iis
- **OpenSSL Commands:** https://www.openssl.org/docs/
- **SSL Best Practices:** https://wiki.mozilla.org/Security/Server_Side_TLS

---

## ✨ Güvenlik İpuçları

1. **Strong Cipher Suites:** IIS'de güçlü şifreleme algoritmaları kullanın
2. **HSTS Header:** HTTP Strict Transport Security aktifleştirin
3. **Certificate Pinning:** Kritik uygulamalar için düşünün
4. **Regular Updates:** Sertifikayı süre dolmadan yenileyin
5. **Private Key Protection:** Private key dosyasını güvenli tutun

---

**Not:** Production ortamında mutlaka HTTPS kullanın! HTTP sadece test için uygundur.
