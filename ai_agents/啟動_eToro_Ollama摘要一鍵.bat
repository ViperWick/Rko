@echo off
chcp 65001 >nul
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\anaconda3;%PATH%"
cd /d "%~dp0.."
echo [%date% %time%] eToro ollama-summarize ...
py -m etoro_trading.scripts ollama-summarize
set "ERR=%ERRORLEVEL%"
echo.
if not "%ERR%"=="0" echo 結束代碼: %ERR%
pause
