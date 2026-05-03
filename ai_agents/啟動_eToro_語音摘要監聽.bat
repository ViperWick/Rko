@echo off
chcp 65001 >nul
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\anaconda3;%PATH%"
cd /d "%~dp0.."
echo 語音監聽中… 請說「執行摘要」等。按 Ctrl+C 結束。
echo.
py -m etoro_trading.scripts listen-ollama-summarize
pause
