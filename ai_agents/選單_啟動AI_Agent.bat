@echo off
chcp 65001 >nul
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\anaconda3;%PATH%"
set "ROOT=%~dp0.."
cd /d "%ROOT%"

:menu
cls
echo ============================================================
echo   AI Agents 選單（入口：ai_agents 資料夾）
echo   實際程式在 etoro_trading / local_agent_demo / 系統 Ollama
echo ============================================================
echo.
echo   1  eToro 語音監聽 — 說「執行摘要」等（視窗常駐，Ctrl+C 結束）
echo   2  eToro 一鍵 Ollama 摘要（跑一次，需 Ollama + daily_*.log）
echo   3  教學 Agent — local_agent_demo（Ollama + 讀檔工具示範）
echo   4  開啟 Ollama 桌面程式（聊天用）
echo.
echo   0  結束
echo.
set /p "CHOICE=請輸入選項後 Enter: "

if "%CHOICE%"=="0" exit /b 0
if "%CHOICE%"=="1" goto voice
if "%CHOICE%"=="2" goto summarize
if "%CHOICE%"=="3" goto demo
if "%CHOICE%"=="4" goto ollama_app

echo 無效選項。
timeout /t 2 >nul
goto menu

:voice
echo.
echo --- 語音監聽（請保持此視窗開啟）---
py -m etoro_trading.scripts listen-ollama-summarize
goto done

:summarize
echo.
echo --- Ollama 摘要 ---
py -m etoro_trading.scripts ollama-summarize
goto done

:demo
echo.
echo --- local_agent_demo（預設內建範例問題，可改 agent.py）---
py local_agent_demo\agent.py
goto done

:ollama_app
echo.
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\Ollama.exe"
if exist "%OLLAMA_EXE%" (
  start "" "%OLLAMA_EXE%"
  echo 已嘗試啟動 Ollama。
) else (
  echo 找不到預設路徑：%OLLAMA_EXE%
  echo 請從開始選單手動開啟 Ollama，或將 ollama 加入 PATH 後改用 start ollama
)
goto done

:done
echo.
pause
goto menu
