# IIS SSL Certificate Setup Script
# SSL sertifikasını IIS'e kurar

Write-Host "=== IIS SSL Certificate Setup ===" -ForegroundColor Green
Write-Host ""

# Yönetici yetkisi kontrolü
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "HATA: Bu script yönetici yetkileri ile çalıştırılmalıdır!" -ForegroundColor Red
    exit 1
}

# Sertifika dosyası yolu
$pfxPath = Read-Host "PFX dosyasının tam yolunu girin"
if (-not (Test-Path $pfxPath)) {
    Write-Host "HATA: Dosya bulunamadı: $pfxPath" -ForegroundColor Red
    exit 1
}

# Sertifika şifresi
$pfxPassword = Read-Host "PFX şifresini girin" -AsSecureString

Write-Host ""
Write-Host "1. Sertifika import ediliyor..." -ForegroundColor Cyan

try {
    # Sertifikayı Local Machine store'una import et
    $cert = Import-PfxCertificate -FilePath $pfxPath `
        -CertStoreLocation Cert:\LocalMachine\My `
        -Password $pfxPassword

    Write-Host "   ✓ Sertifika başarıyla import edildi" -ForegroundColor Green
    Write-Host "   → Thumbprint: $($cert.Thumbprint)" -ForegroundColor Yellow
    Write-Host "   → Subject: $($cert.Subject)" -ForegroundColor Yellow
    Write-Host "   → Expiration: $($cert.NotAfter)" -ForegroundColor Yellow

    # IIS modülünü yükle
    Import-Module WebAdministration -ErrorAction Stop

    Write-Host ""
    Write-Host "2. IIS binding ekleniyor..." -ForegroundColor Cyan

    $siteName = "WarAndSer"
    $site = Get-Website -Name $siteName -ErrorAction SilentlyContinue

    if (-not $site) {
        Write-Host "   ✗ Site bulunamadı: $siteName" -ForegroundColor Red
        exit 1
    }

    # Mevcut HTTPS binding var mı kontrol et
    $existingBinding = Get-WebBinding -Name $siteName -Protocol "https" -ErrorAction SilentlyContinue

    if ($existingBinding) {
        Write-Host "   ! Mevcut HTTPS binding kaldırılıyor..." -ForegroundColor Yellow
        Remove-WebBinding -Name $siteName -Protocol "https" -ErrorAction SilentlyContinue
    }

    # Yeni HTTPS binding ekle
    New-WebBinding -Name $siteName `
        -Protocol "https" `
        -Port 443 `
        -IPAddress "*" `
        -SslFlags 0

    # Sertifikayı binding'e ata
    $binding = Get-WebBinding -Name $siteName -Protocol "https"
    $binding.AddSslCertificate($cert.Thumbprint, "my")

    Write-Host "   ✓ HTTPS binding başarıyla eklendi" -ForegroundColor Green

    Write-Host ""
    Write-Host "3. Django ayarları güncelleniyor..." -ForegroundColor Cyan
    Write-Host "   → .env dosyasında USE_HTTPS=True olarak ayarlayın" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "=== SSL Kurulumu Tamamlandı ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test için:" -ForegroundColor Cyan
    Write-Host "   https://yourdomain.com" -ForegroundColor White
    Write-Host "   https://localhost" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host "   ✗ Hata: $_" -ForegroundColor Red
    exit 1
}
