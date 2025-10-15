# IIS Health Check Script
# Django uygulamasının sağlık kontrolünü yapar

Write-Host "=== WarAndSer Health Check ===" -ForegroundColor Green
Write-Host ""

$checks = @()
$failures = 0

# Function to add check result
function Add-CheckResult {
    param($Name, $Status, $Message)
    $script:checks += [PSCustomObject]@{
        Check = $Name
        Status = $Status
        Message = $Message
    }
    if ($Status -eq "FAIL") {
        $script:failures++
    }
}

# 1. IIS Service Check
Write-Host "1. IIS Servisi kontrol ediliyor..." -ForegroundColor Cyan
$iisService = Get-Service W3SVC -ErrorAction SilentlyContinue
if ($iisService -and $iisService.Status -eq 'Running') {
    Add-CheckResult "IIS Service" "PASS" "Running"
    Write-Host "   ✓ IIS çalışıyor" -ForegroundColor Green
} else {
    Add-CheckResult "IIS Service" "FAIL" "Not running or not found"
    Write-Host "   ✗ IIS çalışmıyor!" -ForegroundColor Red
}

# 2. Site Status Check
Write-Host "2. Site durumu kontrol ediliyor..." -ForegroundColor Cyan
Import-Module WebAdministration -ErrorAction SilentlyContinue
$site = Get-Website -Name "WarAndSer" -ErrorAction SilentlyContinue
if ($site) {
    if ($site.State -eq 'Started') {
        Add-CheckResult "Website" "PASS" "Started"
        Write-Host "   ✓ Site başlatılmış" -ForegroundColor Green
    } else {
        Add-CheckResult "Website" "FAIL" "Not started: $($site.State)"
        Write-Host "   ✗ Site durumu: $($site.State)" -ForegroundColor Red
    }
} else {
    Add-CheckResult "Website" "FAIL" "Site not found"
    Write-Host "   ✗ Site bulunamadı!" -ForegroundColor Red
}

# 3. Python Virtual Environment Check
Write-Host "3. Python sanal ortamı kontrol ediliyor..." -ForegroundColor Cyan
$pythonPath = "C:\Konnektom\WarAndSer\venv\Scripts\python.exe"
if (Test-Path $pythonPath) {
    Add-CheckResult "Python Venv" "PASS" "Found"
    Write-Host "   ✓ Python sanal ortamı mevcut" -ForegroundColor Green

    # Python version
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host "   → $pythonVersion" -ForegroundColor Yellow
} else {
    Add-CheckResult "Python Venv" "FAIL" "Not found"
    Write-Host "   ✗ Python sanal ortamı bulunamadı!" -ForegroundColor Red
}

# 4. PostgreSQL Service Check
Write-Host "4. PostgreSQL servisi kontrol ediliyor..." -ForegroundColor Cyan
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($pgService) {
    if ($pgService.Status -eq 'Running') {
        Add-CheckResult "PostgreSQL" "PASS" "Running"
        Write-Host "   ✓ PostgreSQL çalışıyor" -ForegroundColor Green
    } else {
        Add-CheckResult "PostgreSQL" "FAIL" "Not running"
        Write-Host "   ✗ PostgreSQL çalışmıyor!" -ForegroundColor Red
    }
} else {
    Add-CheckResult "PostgreSQL" "FAIL" "Service not found"
    Write-Host "   ✗ PostgreSQL servisi bulunamadı!" -ForegroundColor Red
}

# 5. Required Folders Check
Write-Host "5. Gerekli klasörler kontrol ediliyor..." -ForegroundColor Cyan
$folders = @{
    "Static" = "C:\inetpub\wwwroot\warandser\static"
    "Media" = "C:\inetpub\wwwroot\warandser\media"
    "Logs" = "C:\inetpub\wwwroot\warandser\logs"
}

$allFoldersExist = $true
foreach ($folder in $folders.GetEnumerator()) {
    if (Test-Path $folder.Value) {
        Write-Host "   ✓ $($folder.Key): OK" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $($folder.Key): MISSING - $($folder.Value)" -ForegroundColor Red
        $allFoldersExist = $false
    }
}

if ($allFoldersExist) {
    Add-CheckResult "Folders" "PASS" "All exist"
} else {
    Add-CheckResult "Folders" "FAIL" "Some folders missing"
}

# 6. .env File Check
Write-Host "6. .env dosyası kontrol ediliyor..." -ForegroundColor Cyan
$envFile = "C:\Konnektom\WarAndSer\.env"
if (Test-Path $envFile) {
    Add-CheckResult ".env File" "PASS" "Exists"
    Write-Host "   ✓ .env dosyası mevcut" -ForegroundColor Green

    # Check for required variables
    $requiredVars = @("SECRET_KEY", "DB_NAME", "DB_PASSWORD")
    $envContent = Get-Content $envFile -Raw
    foreach ($var in $requiredVars) {
        if ($envContent -match $var) {
            Write-Host "   ✓ $var ayarlanmış" -ForegroundColor Green
        } else {
            Write-Host "   ✗ $var eksik!" -ForegroundColor Red
        }
    }
} else {
    Add-CheckResult ".env File" "FAIL" "Not found"
    Write-Host "   ✗ .env dosyası bulunamadı!" -ForegroundColor Red
}

# 7. web.config Check
Write-Host "7. web.config dosyası kontrol ediliyor..." -ForegroundColor Cyan
$webConfig = "C:\Konnektom\WarAndSer\web.config"
if (Test-Path $webConfig) {
    Add-CheckResult "web.config" "PASS" "Exists"
    Write-Host "   ✓ web.config mevcut" -ForegroundColor Green
} else {
    Add-CheckResult "web.config" "FAIL" "Not found"
    Write-Host "   ✗ web.config bulunamadı!" -ForegroundColor Red
}

# 8. HTTP Response Check
Write-Host "8. HTTP yanıtı kontrol ediliyor..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Add-CheckResult "HTTP Response" "PASS" "200 OK"
        Write-Host "   ✓ Site HTTP 200 döndü" -ForegroundColor Green
    } else {
        Add-CheckResult "HTTP Response" "WARN" "Status: $($response.StatusCode)"
        Write-Host "   ! Status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Add-CheckResult "HTTP Response" "FAIL" $_.Exception.Message
    Write-Host "   ✗ HTTP hatası: $($_.Exception.Message)" -ForegroundColor Red
}

# 9. Recent Errors Check
Write-Host "9. Son hatalar kontrol ediliyor..." -ForegroundColor Cyan
$errorLog = "C:\inetpub\wwwroot\warandser\logs\django_error.log"
if (Test-Path $errorLog) {
    $recentErrors = Get-Content $errorLog -Tail 20 | Select-String -Pattern "ERROR|CRITICAL"
    if ($recentErrors.Count -gt 0) {
        Add-CheckResult "Recent Errors" "WARN" "$($recentErrors.Count) errors found"
        Write-Host "   ! Son 20 satırda $($recentErrors.Count) hata bulundu" -ForegroundColor Yellow
    } else {
        Add-CheckResult "Recent Errors" "PASS" "No recent errors"
        Write-Host "   ✓ Son hatalarda sorun yok" -ForegroundColor Green
    }
} else {
    Add-CheckResult "Recent Errors" "INFO" "Log file not found"
    Write-Host "   → Log dosyası henüz oluşturulmamış" -ForegroundColor Yellow
}

# 10. Disk Space Check
Write-Host "10. Disk alanı kontrol ediliyor..." -ForegroundColor Cyan
$drive = Get-PSDrive C
$freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
$totalSpaceGB = [math]::Round(($drive.Free + $drive.Used) / 1GB, 2)
$usedPercent = [math]::Round((($drive.Used) / ($drive.Free + $drive.Used)) * 100, 2)

Write-Host "   → C:\ kullanılabilir: $freeSpaceGB GB / $totalSpaceGB GB (%$usedPercent kullanımda)" -ForegroundColor Yellow

if ($freeSpaceGB -gt 10) {
    Add-CheckResult "Disk Space" "PASS" "$freeSpaceGB GB free"
    Write-Host "   ✓ Yeterli disk alanı var" -ForegroundColor Green
} elseif ($freeSpaceGB -gt 5) {
    Add-CheckResult "Disk Space" "WARN" "Low: $freeSpaceGB GB"
    Write-Host "   ! Disk alanı azalıyor" -ForegroundColor Yellow
} else {
    Add-CheckResult "Disk Space" "FAIL" "Critical: $freeSpaceGB GB"
    Write-Host "   ✗ Disk alanı kritik seviyede!" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "=== Özet ===" -ForegroundColor Green
Write-Host ""

$checks | Format-Table -AutoSize

$passCount = ($checks | Where-Object {$_.Status -eq "PASS"}).Count
$warnCount = ($checks | Where-Object {$_.Status -eq "WARN"}).Count
$failCount = ($checks | Where-Object {$_.Status -eq "FAIL"}).Count
$totalCount = $checks.Count

Write-Host "Toplam Kontrol: $totalCount" -ForegroundColor White
Write-Host "Başarılı: $passCount" -ForegroundColor Green
if ($warnCount -gt 0) { Write-Host "Uyarı: $warnCount" -ForegroundColor Yellow }
if ($failCount -gt 0) { Write-Host "Başarısız: $failCount" -ForegroundColor Red }

Write-Host ""

if ($failCount -eq 0 -and $warnCount -eq 0) {
    Write-Host "✓ Tüm kontroller başarılı! Sistem sağlıklı." -ForegroundColor Green
    exit 0
} elseif ($failCount -eq 0) {
    Write-Host "! Bazı uyarılar var. Kontrol edin." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "✗ Bazı kontroller başarısız! Hemen müdahale gerekiyor." -ForegroundColor Red
    exit 1
}
