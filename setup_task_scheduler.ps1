# PowerShell Script to Import Service Due Notifications Task
# Run this script as Administrator to schedule automatic service notifications

Write-Host "=== GarantiVeServis - Service Due Notifications Task Scheduler ===" -ForegroundColor Green
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

# Define paths
$projectPath = "D:\GarantiVeServis"
$xmlFile = "$projectPath\schedule_service_due_notifications.xml"
$taskName = "GarantiVeServis-ServiceDueNotifications"

Write-Host "Project Path: $projectPath" -ForegroundColor Cyan
Write-Host "XML File: $xmlFile" -ForegroundColor Cyan
Write-Host "Task Name: $taskName" -ForegroundColor Cyan
Write-Host ""

# Check if XML file exists
if (-not (Test-Path $xmlFile)) {
    Write-Host "ERROR: XML file not found: $xmlFile" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Python virtual environment exists
$pythonExe = "$projectPath\venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python executable not found: $pythonExe" -ForegroundColor Red
    Write-Host "Please make sure the virtual environment is set up correctly." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Django project exists
$manageFile = "$projectPath\manage.py"
if (-not (Test-Path $manageFile)) {
    Write-Host "ERROR: Django manage.py not found: $manageFile" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "All required files found. Proceeding with task creation..." -ForegroundColor Green
Write-Host ""

try {
    # Remove existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task: $taskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Existing task removed successfully." -ForegroundColor Green
    }

    # Import the new task
    Write-Host "Importing new task from XML file..." -ForegroundColor Yellow
    Register-ScheduledTask -TaskName $taskName -Xml (Get-Content $xmlFile | Out-String)
    
    Write-Host "" 
    Write-Host "✅ Task created successfully!" -ForegroundColor Green
    Write-Host "" 
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  - Name: $taskName" -ForegroundColor White
    Write-Host "  - Schedule: Daily at 9:00 AM" -ForegroundColor White
    Write-Host "  - Command: $pythonExe" -ForegroundColor White
    Write-Host "  - Arguments: manage.py send_service_due_notifications" -ForegroundColor White
    Write-Host "  - Working Directory: $projectPath" -ForegroundColor White
    Write-Host ""
    
    # Test the task
    Write-Host "Testing the task..." -ForegroundColor Yellow
    $testResult = Start-ScheduledTask -TaskName $taskName -PassThru
    Start-Sleep -Seconds 3
    
    $taskInfo = Get-ScheduledTask -TaskName $taskName
    $taskState = $taskInfo.State
    
    Write-Host "Task State: $taskState" -ForegroundColor Cyan
    
    if ($taskState -eq "Ready") {
        Write-Host "✅ Task test completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Task may need attention. Current state: $taskState" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "=== Next Steps ===" -ForegroundColor Cyan
    Write-Host "1. You can view the task in Task Scheduler (taskschd.msc)" -ForegroundColor White
    Write-Host "2. The task will run automatically every day at 9:00 AM" -ForegroundColor White
    Write-Host "3. To test manually, run: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host "4. To disable: Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host "5. To remove: Unregister-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ ERROR occurred while creating the task:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "1. Make sure you're running as Administrator" -ForegroundColor White
    Write-Host "2. Check if the XML file is valid" -ForegroundColor White
    Write-Host "3. Verify all file paths in the XML are correct" -ForegroundColor White
    Write-Host "4. Try running the Django command manually first" -ForegroundColor White
    Write-Host ""
}

Write-Host "Script completed. Press Enter to exit..." -ForegroundColor Gray
Read-Host
