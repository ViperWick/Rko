@echo off
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\miniconda3;%PATH%"
cd /d "%~dp0\..\.."
py -m etoro_trading.scripts today-summary
pause

