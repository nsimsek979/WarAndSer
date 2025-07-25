# PowerShell Script to Remove Service Due Notifications Task
# Run this script as Administrator to remove the scheduled task

Write-Host "=== GarantiVeServis - Remove Service Due Notifications Task ===" -ForegroundColor Red
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click on PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$taskName = "GarantiVeServis-ServiceDueNotifications"

Write-Host "Task Name: $taskName" -ForegroundColor Cyan
Write-Host ""

try {
    # Check if task exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if (-not $existingTask) {
        Write-Host "✅ Task '$taskName' does not exist or has already been removed." -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "Found existing task. Removing..." -ForegroundColor Yellow
        
        # Stop the task if it's running
        $taskState = $existingTask.State
        if ($taskState -eq "Running") {
            Write-Host "Task is currently running. Stopping..." -ForegroundColor Yellow
            Stop-ScheduledTask -TaskName $taskName
            Start-Sleep -Seconds 2
        }
        
        # Remove the task
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        
        Write-Host "✅ Task '$taskName' has been successfully removed!" -ForegroundColor Green
        Write-Host ""
    }
    
    Write-Host "=== Verification ===" -ForegroundColor Cyan
    $verifyTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $verifyTask) {
        Write-Host "✅ Confirmed: Task has been completely removed from Task Scheduler." -ForegroundColor Green
    } else {
        Write-Host "⚠️  Warning: Task may still exist. Please check Task Scheduler manually." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ ERROR occurred while removing the task:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need to remove the task manually:" -ForegroundColor Yellow
    Write-Host "1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
    Write-Host "2. Navigate to Task Scheduler Library" -ForegroundColor White
    Write-Host "3. Look for '$taskName'" -ForegroundColor White
    Write-Host "4. Right-click and select Delete" -ForegroundColor White
    Write-Host ""
}

Write-Host "Script completed. Press Enter to exit..." -ForegroundColor Gray
Read-Host
