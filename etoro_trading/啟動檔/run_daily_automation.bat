@echo off
chcp 65001 >nul
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\anaconda3;%PATH%"
cd /d "%~dp0"
echo Log: etoro_trading\data\automation_logs\
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\run_daily_automation.ps1" %*
echo.
pause
