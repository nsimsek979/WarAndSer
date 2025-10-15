# PostgreSQL Database Setup Script
# warandser_db veritabanını ve kullanıcısını oluşturur

Write-Host "=== PostgreSQL Database Setup ===" -ForegroundColor Green
Write-Host ""

# PostgreSQL bin dizinini bul
$pgVersions = @("16", "15", "14", "13", "12")
$psqlPath = $null

foreach ($version in $pgVersions) {
    $testPath = "C:\Program Files\PostgreSQL\$version\bin\psql.exe"
    if (Test-Path $testPath) {
        $psqlPath = $testPath
        Write-Host "✓ PostgreSQL $version bulundu" -ForegroundColor Green
        break
    }
}

if (-not $psqlPath) {
    Write-Host "✗ PostgreSQL bulunamadı!" -ForegroundColor Red
    Write-Host "PostgreSQL'in kurulu olduğundan emin olun." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "PostgreSQL veritabanı oluşturulacak:" -ForegroundColor Cyan
Write-Host "  Database: warandser_db" -ForegroundColor White
Write-Host "  User: warandser_user" -ForegroundColor White
Write-Host "  Password: Konnektom123*" -ForegroundColor White
Write-Host ""

$continue = Read-Host "Devam etmek istiyor musunuz? (E/H)"
if ($continue -ne "E" -and $continue -ne "e") {
    Write-Host "İptal edildi." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "PostgreSQL postgres kullanıcı şifresini girin:" -ForegroundColor Cyan

# SQL komutlarını geçici dosyaya yaz
$sqlFile = Join-Path $env:TEMP "warandser_setup.sql"
$sqlContent = @"
-- Veritabanı oluştur
CREATE DATABASE warandser_db;

-- Kullanıcı oluştur
CREATE USER warandser_user WITH PASSWORD 'Konnektom123*';

-- İzinleri ayarla
ALTER ROLE warandser_user SET client_encoding TO 'utf8';
ALTER ROLE warandser_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE warandser_user SET timezone TO 'Europe/Istanbul';

-- Tüm izinleri ver
GRANT ALL PRIVILEGES ON DATABASE warandser_db TO warandser_user;

-- PostgreSQL 15+ için ek izinler (schema)
\c warandser_db
GRANT ALL ON SCHEMA public TO warandser_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO warandser_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO warandser_user;
"@

Set-Content -Path $sqlFile -Value $sqlContent

Write-Host ""
Write-Host "SQL komutları çalıştırılıyor..." -ForegroundColor Cyan

try {
    # psql komutunu çalıştır
    & $psqlPath -U postgres -f $sqlFile

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=== Kurulum Başarılı! ===" -ForegroundColor Green
        Write-Host ""
        Write-Host "Veritabanı Bilgileri:" -ForegroundColor Cyan
        Write-Host "  Database: warandser_db" -ForegroundColor White
        Write-Host "  User: warandser_user" -ForegroundColor White
        Write-Host "  Password: Konnektom123*" -ForegroundColor White
        Write-Host "  Host: localhost" -ForegroundColor White
        Write-Host "  Port: 5432" -ForegroundColor White
        Write-Host ""
        Write-Host "Sonraki Adım:" -ForegroundColor Yellow
        Write-Host "  .env dosyasını oluşturun ve yukarıdaki bilgileri girin" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "✗ Hata oluştu!" -ForegroundColor Red
        Write-Host "Muhtemelen veritabanı zaten mevcut." -ForegroundColor Yellow
        Write-Host "Devam etmek için .env dosyasını yapılandırın." -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "✗ Hata: $_" -ForegroundColor Red
} finally {
    # Geçici dosyayı sil
    Remove-Item -Path $sqlFile -ErrorAction SilentlyContinue
}
