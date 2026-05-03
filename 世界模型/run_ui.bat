@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 優先使用 Miniconda/Anaconda 的 Python
if exist "C:\Users\User\miniconda3\python.exe" (
    set "PY=C:\Users\User\miniconda3\python.exe"
) else if exist "C:\Users\User\Anaconda3\python.exe" (
    set "PY=C:\Users\User\Anaconda3\python.exe"
) else (
    set "PY=python"
)

echo ========================================
echo   世界模型 - 統一城市 UI
echo ========================================
echo.
echo 正在啟動，瀏覽器將自動開啟...
echo 若未開啟，請手動前往: http://localhost:8501
echo 關閉此視窗即可結束程式
echo ========================================
echo.

"%PY%" -m streamlit run app.py
if errorlevel 1 (
    echo.
    echo 啟動失敗
    pause
)
