# PKCS#7 to PFX Converter
param(
    [string]$P7bFile = "certificate.p7b",
    [string]$KeyFile = "private.key",
    [string]$PfxFile = "certificate.pfx",
    [string]$Password = "YourPassword123"
)

Write-Host "PKCS#7 to PFX Converter" -ForegroundColor Cyan

# OpenSSL kontrol et
$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $openssl) {
    Write-Host "❌ OpenSSL bulunamadı!" -ForegroundColor Red
    Write-Host "📥 İndir: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor Yellow
    Write-Host "💡 Alternatif: IIS Manager'da manuel import" -ForegroundColor Yellow
    exit 1
}

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

# PKCS#7'den PFX oluştur
Write-Host "🔄 PFX dosyası oluşturuluyor..." -ForegroundColor Yellow
$command = "openssl pkcs12 -export -out `"$PfxFile`" -inkey `"$KeyFile`" -in `"$P7bFile`" -password pass:`"$Password`""

try {
    Invoke-Expression $command
    Write-Host "✅ PFX dosyası oluşturuldu: $PfxFile" -ForegroundColor Green
    Write-Host "🔑 Password: $Password" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Sonraki adımlar:" -ForegroundColor Yellow
    Write-Host "   1. IIS Manager aç" -ForegroundColor White
    Write-Host "   2. Server Certificates -> Import" -ForegroundColor White
    Write-Host "   3. PFX dosyasını seç: $PfxFile" -ForegroundColor White
    Write-Host "   4. Password gir: $Password" -ForegroundColor White
    Write-Host "   5. Site binding'de SSL sertifikasını ata" -ForegroundColor White
} catch {
    Write-Host "❌ PFX oluşturma hatası: $($_.Exception.Message)" -ForegroundColor Red
}

