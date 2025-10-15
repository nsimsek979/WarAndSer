# Collect Static Files Script
# Django static dosyalarını toplar

Write-Host "=== Static Dosyalar Toplanıyor ===" -ForegroundColor Green

$projectPath = "C:\Konnektom\WarAndSer"
$pythonExe = "$projectPath\venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "HATA: Python sanal ortamı bulunamadı!" -ForegroundColor Red
    Write-Host "Yol: $pythonExe" -ForegroundColor Yellow
    exit 1
}

Push-Location $projectPath
try {
    $env:DJANGO_SETTINGS_MODULE = "gvs.settings_iis_prod"
    Write-Host "→ Static dosyalar toplanıyor..." -ForegroundColor Cyan
    & $pythonExe manage.py collectstatic --noinput --clear

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Static dosyalar başarıyla toplandı!" -ForegroundColor Green
    } else {
        Write-Host "✗ Hata oluştu!" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}
