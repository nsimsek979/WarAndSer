# Scheduled Backup Setup Script
# Windows Task Scheduler'da otomatik backup görevi oluşturur

Write-Host "=== Scheduled Backup Setup ===" -ForegroundColor Green

# Yönetici yetkisi kontrolü
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "HATA: Bu script yönetici yetkileri ile çalıştırılmalıdır!" -ForegroundColor Red
    exit 1
}

$scriptPath = "$PSScriptRoot\postgres_backup.ps1"
$taskName = "WarAndSer_PostgreSQL_Backup"

Write-Host "→ Scheduled task oluşturuluyor: $taskName" -ForegroundColor Cyan

# Mevcut task'ı kontrol et
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "! Task zaten mevcut, kaldırılıyor..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Task action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

# Task trigger - Her gün saat 02:00'de
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# Task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable $false

# Task principal - SYSTEM hesabı ile çalışır
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Task'ı kaydet
Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "WarAndSer PostgreSQL günlük otomatik yedekleme"

Write-Host "✓ Scheduled task oluşturuldu!" -ForegroundColor Green
Write-Host ""
Write-Host "Görev Bilgileri:" -ForegroundColor Cyan
Write-Host "   İsim: $taskName" -ForegroundColor White
Write-Host "   Çalışma Zamanı: Her gün saat 02:00" -ForegroundColor White
Write-Host "   Script: $scriptPath" -ForegroundColor White
Write-Host ""
Write-Host "Görevi görmek için: taskschd.msc" -ForegroundColor Yellow
