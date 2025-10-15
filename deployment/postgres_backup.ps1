# PostgreSQL Backup Script
# PostgreSQL veritabanını yedekler

param(
    [string]$BackupPath = "C:\Backups\PostgreSQL",
    [string]$DbName = "warandser_db",
    [string]$DbUser = "postgres",
    [int]$RetentionDays = 7
)

Write-Host "=== PostgreSQL Backup ===" -ForegroundColor Green

# Backup klasörü oluştur
if (-not (Test-Path $BackupPath)) {
    New-Item -Path $BackupPath -ItemType Directory -Force | Out-Null
    Write-Host "✓ Backup klasörü oluşturuldu: $BackupPath" -ForegroundColor Green
}

# Tarih damgası
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $BackupPath "$DbName`_$timestamp.sql"

Write-Host "→ Veritabanı yedekleniyor: $DbName" -ForegroundColor Cyan
Write-Host "   Hedef: $backupFile" -ForegroundColor Yellow

# PostgreSQL bin dizinini PATH'e ekle (gerekirse)
$pgPath = "C:\Program Files\PostgreSQL\14\bin"  # Versiyonunuza göre güncelleyin
if (Test-Path $pgPath) {
    $env:PATH = "$pgPath;$env:PATH"
}

# Backup al
try {
    & pg_dump -U $DbUser -h localhost -F p -f $backupFile $DbName

    if ($LASTEXITCODE -eq 0) {
        $fileSize = (Get-Item $backupFile).Length / 1MB
        Write-Host "✓ Backup başarıyla oluşturuldu!" -ForegroundColor Green
        Write-Host "   Boyut: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
    } else {
        Write-Host "✗ Backup hatası!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Hata: $_" -ForegroundColor Red
    exit 1
}

# Eski backupları temizle
Write-Host "→ Eski backuplar temizleniyor (>$RetentionDays gün)..." -ForegroundColor Cyan
$oldBackups = Get-ChildItem -Path $BackupPath -Filter "*.sql" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) }

foreach ($oldBackup in $oldBackups) {
    Remove-Item $oldBackup.FullName -Force
    Write-Host "   ✓ Silindi: $($oldBackup.Name)" -ForegroundColor Yellow
}

Write-Host "✓ Backup işlemi tamamlandı!" -ForegroundColor Green
