# Manual Certificate Import Script
param(
    [string]$P7bFile = "PKCS7.p7b",
    [string]$KeyFile = "private.key",
    [string]$Password = "YourPassword123",
    [string]$FriendlyName = "eqpro.konnektomdev.com"
)

Write-Host "Manual Certificate Import" -ForegroundColor Cyan

# Dosyalar var mı kontrol et
if (-not (Test-Path $P7bFile)) {
    Write-Host "❌ PKCS#7 dosyası bulunamadı: $P7bFile" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $KeyFile)) {
    Write-Host "❌ Private key dosyası bulunamadı: $KeyFile" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dosyalar bulundu" -ForegroundColor Green
Write-Host "📁 PKCS#7: $P7bFile" -ForegroundColor White
Write-Host "🔑 Private Key: $KeyFile" -ForegroundColor White
Write-Host "🔒 Password: $Password" -ForegroundColor White

Write-Host ""
Write-Host "📋 IIS Manager'da yapılacaklar:" -ForegroundColor Yellow
Write-Host "   1. IIS Manager aç (inetmgr)" -ForegroundColor White
Write-Host "   2. Server Certificates -> Import..." -ForegroundColor White
Write-Host "   3. Certificate File: $P7bFile" -ForegroundColor White
Write-Host "   4. Private Key File: $KeyFile" -ForegroundColor White
Write-Host "   5. Password: $Password" -ForegroundColor White
Write-Host "   6. Friendly Name: $FriendlyName" -ForegroundColor White
Write-Host "   7. OK" -ForegroundColor White
Write-Host ""
Write-Host "🌐 IIS Manager'ı açmak için:" -ForegroundColor Cyan
Write-Host "   Start-Process 'inetmgr'" -ForegroundColor White

# IIS Manager'ı aç
Start-Process "inetmgr"




