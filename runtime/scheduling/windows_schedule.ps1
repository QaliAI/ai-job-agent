# PowerShell Script to Schedule Daily AI Job Agent Search on Windows Task Scheduler
# Run in PowerShell: powershell -ExecutionPolicy Bypass -File .\runtime\scheduling\windows_schedule.ps1

$TaskName = "AIJobAgentDailySearch"
$ScriptDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PythonPath = (Get-Command python).Source
$ActionScript = Join-Path $ScriptDir "scripts\daily_workflow.py"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "   Scheduling AI Job Agent Daily Search on Windows   " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Project Directory: $ScriptDir"
Write-Host "Python Executable: $PythonPath"
Write-Host "Script Target:     $ActionScript"
Write-Host ""

# Define Task Action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ActionScript`"" -WorkingDirectory $ScriptDir

# Define Task Trigger (Daily at 8:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM

# Define Task Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the Scheduled Task
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily Autonomous Job Search & Morning Brief by AI Job Agent"
    Write-Host "🎉 Successfully registered scheduled task '$TaskName'!" -ForegroundColor Green
    Write-Host "   AI Job Agent will run every morning at 8:00 AM." -ForegroundColor Green
    Write-Host "   Your report will be ready in output\latest_brief.md." -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to register scheduled task: $_" -ForegroundColor Red
}
Write-Host "=======================================================" -ForegroundColor Cyan
