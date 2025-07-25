# Service Due Notifications - Automatic Scheduling

This directory contains the necessary files to automatically schedule service due notifications using Windows Task Scheduler.

## Files Overview

### 1. `schedule_service_due_notifications.xml`
Windows Task Scheduler XML configuration file that defines:
- **Schedule**: Daily at 9:00 AM
- **Command**: Runs the Django management command to send service notifications
- **Settings**: Network-aware, allows manual execution, 1-hour timeout

### 2. `setup_task_scheduler.ps1`
PowerShell script to install and configure the scheduled task:
- Checks for Administrator privileges
- Validates all required files and paths
- Imports the XML configuration into Task Scheduler
- Tests the task execution
- Provides next steps and troubleshooting tips

### 3. `remove_task_scheduler.ps1`
PowerShell script to safely remove the scheduled task:
- Stops running task if necessary
- Removes the task from Task Scheduler
- Verifies successful removal

## Installation Instructions

### Step 1: Prerequisites
Make sure you have:
- ✅ Django project is working (`python manage.py check` passes)
- ✅ Virtual environment is activated
- ✅ Email settings are configured in Django settings
- ✅ Database contains installations with service due dates

### Step 2: Install the Scheduled Task
1. **Open PowerShell as Administrator**
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Navigate to project directory**
   ```powershell
   cd D:\GarantiVeServis
   ```

3. **Run the setup script**
   ```powershell
   .\setup_task_scheduler.ps1
   ```

4. **Follow the on-screen instructions**
   - The script will validate all requirements
   - Import the task into Task Scheduler
   - Test the task execution
   - Display success confirmation

### Step 3: Verify Installation
1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter
   - Navigate to "Task Scheduler Library"
   - Look for "GarantiVeServis-ServiceDueNotifications"

2. **Check task properties**
   - Right-click the task → Properties
   - Verify the schedule (Daily at 9:00 AM)
   - Check the Actions tab for correct command path

3. **Test manual execution**
   ```powershell
   Start-ScheduledTask -TaskName "GarantiVeServis-ServiceDueNotifications"
   ```

## How It Works

### Daily Execution Flow
1. **9:00 AM every day**: Windows Task Scheduler triggers
2. **Command executed**: `python manage.py send_service_due_notifications`
3. **Notification logic**:
   - Checks installations with service due in 15, 7, 3, or 0 days
   - Sends appropriate email notifications to customers
   - Logs all activities for tracking

### Email Notifications
The system sends different types of notifications:
- **15 days before**: Early warning notification
- **7 days before**: Weekly reminder
- **3 days before**: Urgent reminder
- **Day of service**: Critical notification

### Monitoring and Logs
- **Task History**: View in Task Scheduler → History tab
- **Django Logs**: Check your Django logging configuration
- **Email Logs**: Monitor email sending status in logs

## Troubleshooting

### Common Issues

#### 1. Task Not Running
```powershell
# Check task status
Get-ScheduledTask -TaskName "GarantiVeServis-ServiceDueNotifications"

# View last run result
Get-ScheduledTaskInfo -TaskName "GarantiVeServis-ServiceDueNotifications"
```

#### 2. Permission Issues
- Ensure the script was run as Administrator
- Check that the Python executable path is correct
- Verify Django project permissions

#### 3. Path Issues
- Verify Python virtual environment path: `D:\GarantiVeServis\venv\Scripts\python.exe`
- Check Django project path: `D:\GarantiVeServis\manage.py`
- Update XML file if paths are different

#### 4. Email Not Sending
- Test Django email configuration manually
- Check SMTP settings in Django settings
- Verify network connectivity

### Manual Testing
To test the notification system manually:

```bash
# Test in dry-run mode (no emails sent)
python manage.py send_service_due_notifications --dry-run

# Send actual notifications
python manage.py send_service_due_notifications

# Test with specific days
python manage.py send_service_due_notifications --days 15,7,3,0
```

### Updating the Schedule
To change the schedule (e.g., different time):
1. Edit `schedule_service_due_notifications.xml`
2. Update the `<StartBoundary>` time
3. Run `.\setup_task_scheduler.ps1` again

### Removing the Task
To completely remove the scheduled task:
```powershell
.\remove_task_scheduler.ps1
```

## Support

For issues or questions:
1. Check Django logs for errors
2. Review Task Scheduler event logs
3. Test the management command manually
4. Verify email configuration

## Security Considerations

- The task runs with least privileges
- Network connectivity is required for email sending
- Sensitive data (email credentials) should be properly secured in Django settings
- Consider using environment variables for production secrets

---

**Last Updated**: July 25, 2025
**Version**: 1.0
**Compatible with**: Windows 10/11, Windows Server 2016+
