@echo off
chcp 65001 >nul
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\miniconda3;%PATH%"
cd /d "%~dp0.."
echo 啟動 local_agent_demo（需本機 Ollama）...
echo.
py local_agent_demo\agent.py
pause
