# IIS Django Deployment Setup Script
# Bu script IIS uzerinde Django projesini yapilandirir

Write-Host "=== Django IIS Deployment Setup ===" -ForegroundColor Green
Write-Host ""

# Yonetici yetkisi kontrolu
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "HATA: Bu script yonetici yetkileri ile calistirilmalidir!" -ForegroundColor Red
    Write-Host "PowerShell'i 'Run as Administrator' ile acin ve tekrar deneyin." -ForegroundColor Yellow
    exit 1
}

# Proje yolu
$projectPath = "C:\Konnektom\avanti"
$venvPath = "$projectPath\venv"
$pythonExe = "$venvPath\Scripts\python.exe"

# Static ve Media klasorleri
$staticRoot = "C:\inetpub\wwwroot\avanti\static"
$mediaRoot = "C:\inetpub\wwwroot\avanti\media"
$logDir = "C:\inetpub\wwwroot\avanti\logs"

Write-Host "1. Gerekli klasorler olusturuluyor..." -ForegroundColor Cyan
$folders = @($staticRoot, $mediaRoot, $logDir)
foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -Path $folder -ItemType Directory -Force | Out-Null
        Write-Host "   [OK] Olusturuldu: $folder" -ForegroundColor Green
    } else {
        Write-Host "   [OK] Zaten mevcut: $folder" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "2. IIS izinleri ayarlaniyor..." -ForegroundColor Cyan
$identities = @("IIS_IUSRS", "IUSR")
foreach ($folder in $folders) {
    foreach ($identity in $identities) {
        try {
            icacls $folder /grant "${identity}:(OI)(CI)M" /T /Q
            Write-Host "   [OK] $identity icin izin verildi: $folder" -ForegroundColor Green
        } catch {
            Write-Host "   [HATA] $identity icin izin verilemedi: $folder" -ForegroundColor Red
        }
    }
}

# Proje klasorune de izin ver
icacls $projectPath /grant "IIS_IUSRS:(OI)(CI)RX" /T /Q
Write-Host "   [OK] Proje klasorune okuma izni verildi" -ForegroundColor Green

Write-Host ""
Write-Host "3. Python sanal ortami kontrol ediliyor..." -ForegroundColor Cyan
if (-not (Test-Path $pythonExe)) {
    Write-Host "   [HATA] Sanal ortam bulunamadi: $venvPath" -ForegroundColor Red
    Write-Host "   Lutfen once sanal ortami olusturun:" -ForegroundColor Yellow
    Write-Host "   python -m venv venv" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "   [OK] Sanal ortam bulundu" -ForegroundColor Green
}

Write-Host ""
Write-Host "4. Bagimliliklar kontrol ediliyor..." -ForegroundColor Cyan
Write-Host "   [UYARI] Bagimliliklar manuel kurulmali (requirements.txt sorunlu)" -ForegroundColor Yellow
Write-Host "   Lutfen once venv'de bu komutu calistirin:" -ForegroundColor Yellow
Write-Host "   pip install Django psycopg2-binary djangorestframework wfastcgi python-dotenv" -ForegroundColor White

Write-Host ""
Write-Host "5. wfastcgi etkinlestiriliyor..." -ForegroundColor Cyan
try {
    & $pythonExe -m wfastcgi enable 2>&1 | Out-Null
    Write-Host "   [OK] wfastcgi etkinlestirildi" -ForegroundColor Green
} catch {
    Write-Host "   [UYARI] wfastcgi manuel etkinlestirilmeli" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "6. Django migration ve static dosyalar..." -ForegroundColor Cyan
Write-Host "   [UYARI] Bu adimlar .env dosyasi gerektirir" -ForegroundColor Yellow
Write-Host "   Daha sonra manuel calistirilacak:" -ForegroundColor Yellow
Write-Host "   python manage.py migrate" -ForegroundColor White
Write-Host "   python manage.py collectstatic" -ForegroundColor White

Write-Host ""
Write-Host "7. IIS yapılandirmasi..." -ForegroundColor Cyan

# IIS modullerini kontrol et
Import-Module WebAdministration -ErrorAction SilentlyContinue
if ($?) {
    Write-Host "   [OK] IIS PowerShell modulu yuklu" -ForegroundColor Green

    # Site var mi kontrol et
    $siteName = "WarAndSer"
    $site = Get-Website -Name $siteName -ErrorAction SilentlyContinue
    if ($site) {
        Write-Host "   [OK] Site zaten mevcut: $siteName" -ForegroundColor Yellow
        Write-Host "   -> Site yeniden baslatiliyor..." -ForegroundColor Yellow
        Stop-Website -Name $siteName
        Start-Website -Name $siteName
        Write-Host "   [OK] Site yeniden baslatildi" -ForegroundColor Green
    } else {
        Write-Host "   [UYARI] Site bulunamadi: $siteName" -ForegroundColor Yellow
        Write-Host "   IIS Manager'dan manuel olarak olusturmaniz gerekiyor." -ForegroundColor Yellow
        Write-Host "   Rehber icin: IIS_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
    }
} else {
    Write-Host "   [UYARI] IIS PowerShell modulu yuklenemedi" -ForegroundColor Yellow
    Write-Host "   IIS'yi manuel olarak yapilandirmaniz gerekiyor." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Kurulum Tamamlandi ===" -ForegroundColor Green
Write-Host ""
Write-Host "Sonraki Adimlar:" -ForegroundColor Cyan
Write-Host "1. .env dosyasini olusturun ve yapilandirin" -ForegroundColor White
Write-Host "2. web.config dosyasindaki yollari kontrol edin" -ForegroundColor White
Write-Host "3. IIS Manager'da site'i olusturun/kontrol edin" -ForegroundColor White
Write-Host "4. PostgreSQL veritabanini yapilandirin" -ForegroundColor White
Write-Host "5. Detayli rehber icin IIS_DEPLOYMENT_GUIDE.md dosyasina bakin" -ForegroundColor White
Write-Host ""
Write-Host "Log Klasorleri:" -ForegroundColor Cyan
Write-Host "   Django Logs: $logDir" -ForegroundColor White
Write-Host "   IIS Logs: C:\inetpub\logs\LogFiles" -ForegroundColor White
Write-Host ""
