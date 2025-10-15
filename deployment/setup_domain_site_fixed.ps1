# Domain Site Setup Script
param(
    [string]$DomainName = "eqpro.konnektomdev.com",
    [string]$SitePath = "C:\inetpub\wwwroot\warandser",
    [string]$AppPoolName = "WarAndSerAppPool"
)

Write-Host "Domain Site Setup: $DomainName" -ForegroundColor Cyan

# 1. Mevcut site'ı durdur
Write-Host "1. Mevcut site durduruluyor..." -ForegroundColor Yellow
Stop-Website -Name "WarAndSer" -ErrorAction SilentlyContinue

# 2. Yeni site oluştur
Write-Host "2. Yeni domain site oluşturuluyor..." -ForegroundColor Yellow
New-Website -Name "WarAndSer-Domain" -Port 80 -PhysicalPath $SitePath -ApplicationPool $AppPoolName -HostHeader $DomainName

# 3. HTTPS binding ekle (port 443)
Write-Host "3. HTTPS binding ekleniyor..." -ForegroundColor Yellow
New-WebBinding -Name "WarAndSer-Domain" -Protocol "https" -Port 443 -HostHeader $DomainName

# 4. SSL sertifikası atama (manuel yapılacak)
Write-Host "4. SSL sertifikası atanacak (IIS Manager'dan)" -ForegroundColor Yellow

# 5. Site'ı başlat
Write-Host "5. Site başlatılıyor..." -ForegroundColor Yellow
Start-Website -Name "WarAndSer-Domain"

Write-Host ""
Write-Host "Domain site kurulumu tamamlandı!" -ForegroundColor Green
Write-Host "Site: http://$DomainName" -ForegroundColor Cyan
Write-Host "HTTPS: https://$DomainName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Yapılacaklar:" -ForegroundColor Yellow
Write-Host "   1. DNS A record: $DomainName -> [Bu sunucunun IP'si]" -ForegroundColor White
Write-Host "   2. SSL sertifikası kur (IIS Manager -> Bindings -> Edit)" -ForegroundColor White
Write-Host "   3. Django ALLOWED_HOSTS güncelle" -ForegroundColor White
Write-Host "   4. Test: https://$DomainName" -ForegroundColor White
