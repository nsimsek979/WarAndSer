# Domain Site Setup Script
param(
    [string]$DomainName = "eqpro.konnektomdev.com",
    [string]$SitePath = "C:\inetpub\wwwroot\warandser",
    [string]$AppPoolName = "WarAndSerAppPool"
)

Write-Host "🌐 Domain Site Setup: $DomainName" -ForegroundColor Cyan

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
Write-Host "4. SSL sertifikasi atanacak (IIS Manager'dan)" -ForegroundColor Yellow

# 5. URL Rewrite rules ekle (HTTP -> HTTPS)
Write-Host "5. HTTP -> HTTPS redirect ekleniyor..." -ForegroundColor Yellow
$webConfigPath = Join-Path $SitePath "web.config"

# URL Rewrite rules ekle
$urlRewriteConfig = @"
<system.webServer>
  <rewrite>
    <rules>
      <rule name="HTTP to HTTPS redirect" stopProcessing="true">
        <match url="(.*)" />
        <conditions>
          <add input="{HTTPS}" pattern="off" ignoreCase="true" />
        </conditions>
        <action type="Redirect" url="https://{HTTP_HOST}/{R:1}"
                redirectType="Permanent" />
      </rule>
    </rules>
  </rewrite>
</system.webServer>
"@

# Mevcut web.config'e ekle
if (Test-Path $webConfigPath) {
    $content = Get-Content $webConfigPath -Raw
    if ($content -notmatch "HTTP to HTTPS redirect") {
        # URL Rewrite section'ı ekle
        $newContent = $content -replace "</configuration>", "$urlRewriteConfig`n</configuration>"
        Set-Content -Path $webConfigPath -Value $newContent -Encoding UTF8
        Write-Host "   ✅ URL Rewrite rules eklendi" -ForegroundColor Green
    }
}

# 6. Site'ı başlat
Write-Host "6. Site başlatılıyor..." -ForegroundColor Yellow
Start-Website -Name "WarAndSer-Domain"

Write-Host ""
Write-Host "✅ Domain site kurulumu tamamlandı!" -ForegroundColor Green
Write-Host "🌐 Site: http://$DomainName" -ForegroundColor Cyan
Write-Host "🔒 HTTPS: https://$DomainName" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Yapılacaklar:" -ForegroundColor Yellow
Write-Host "   1. DNS A record: $DomainName -> [Bu sunucunun IP'si]" -ForegroundColor White
Write-Host "   2. SSL sertifikası kur (IIS Manager -> Bindings -> Edit)" -ForegroundColor White
Write-Host "   3. Django ALLOWED_HOSTS güncelle" -ForegroundColor White
Write-Host "   4. Test: https://$DomainName" -ForegroundColor White
