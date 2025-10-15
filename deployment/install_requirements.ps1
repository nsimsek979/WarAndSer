# Requirements Installation Script
# Sorunlu paketleri önce binary olarak kurar

Write-Host "=== Python Paketleri Kurulumu ===" -ForegroundColor Green
Write-Host ""

$projectPath = "C:\Konnektom\WarAndSer"
$pythonExe = "$projectPath\venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "HATA: Sanal ortam bulunamadı!" -ForegroundColor Red
    Write-Host "Önce sanal ortam oluşturun: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Push-Location $projectPath
try {
    Write-Host "1. pip, setuptools, wheel güncelleniyor..." -ForegroundColor Cyan
    & $pythonExe -m pip install --upgrade pip setuptools wheel -q
    Write-Host "   ✓ Araçlar güncellendi" -ForegroundColor Green

    Write-Host ""
    Write-Host "2. Kritik paketler kuruluyor (binary)..." -ForegroundColor Cyan

    # Sorunlu paketleri önce binary olarak kur
    $criticalPackages = @(
        "psycopg2-binary==2.9.9",
        "pandas==2.0.3",
        "numpy",
        "pillow"
    )

    foreach ($package in $criticalPackages) {
        Write-Host "   → $package" -ForegroundColor Yellow
        & $pythonExe -m pip install $package --only-binary :all: -q
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ $package kuruldu" -ForegroundColor Green
        } else {
            Write-Host "   ✗ $package kurulamadı" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "3. Diğer paketler kuruluyor..." -ForegroundColor Cyan
    & $pythonExe -m pip install -r requirements.txt --prefer-binary

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Tüm paketler kuruldu" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Bazı paketler kurulamadı" -ForegroundColor Red
        Write-Host "   Detaylar için yukarıdaki hataları kontrol edin" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "4. Kurulumu doğrulama..." -ForegroundColor Cyan

    $testPackages = @(
        "django",
        "psycopg2",
        "pandas",
        "rest_framework"
    )

    foreach ($package in $testPackages) {
        $test = & $pythonExe -c "import $package; print('OK')" 2>$null
        if ($test -eq "OK") {
            Write-Host "   ✓ $package" -ForegroundColor Green
        } else {
            Write-Host "   ✗ $package" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "=== Kurulum Tamamlandı ===" -ForegroundColor Green

} finally {
    Pop-Location
}
