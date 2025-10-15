# IIS Site Restart Script
# Django projesini IIS üzerinde yeniden başlatır

Write-Host "=== IIS Site Restart ===" -ForegroundColor Green

# Yönetici yetkisi kontrolü
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "HATA: Bu script yönetici yetkileri ile çalıştırılmalıdır!" -ForegroundColor Red
    exit 1
}

$siteName = "WarAndSer"

# IIS modülünü yükle
Import-Module WebAdministration -ErrorAction SilentlyContinue

if ($?) {
    Write-Host "Site yeniden başlatılıyor: $siteName" -ForegroundColor Cyan

    # Application Pool'u da yeniden başlat
    $appPoolName = (Get-Website -Name $siteName).ApplicationPool
    if ($appPoolName) {
        Write-Host "Application Pool durduruluyor: $appPoolName" -ForegroundColor Yellow
        Stop-WebAppPool -Name $appPoolName
        Start-Sleep -Seconds 2
        Write-Host "Application Pool başlatılıyor: $appPoolName" -ForegroundColor Yellow
        Start-WebAppPool -Name $appPoolName
    }

    # Site'ı yeniden başlat
    Write-Host "Site durduruluyor: $siteName" -ForegroundColor Yellow
    Stop-Website -Name $siteName
    Start-Sleep -Seconds 2
    Write-Host "Site başlatılıyor: $siteName" -ForegroundColor Yellow
    Start-Website -Name $siteName

    Write-Host "✓ Site başarıyla yeniden başlatıldı!" -ForegroundColor Green
} else {
    Write-Host "HATA: IIS PowerShell modülü yüklenemedi!" -ForegroundColor Red
    Write-Host "IIS'nin düzgün kurulu olduğundan emin olun." -ForegroundColor Yellow
    exit 1
}
