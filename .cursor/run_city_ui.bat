@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   世界模型 - 統一城市 UI
echo ========================================
echo.

REM 優先從世界模型目錄執行
if exist "世界模型\app.py" (
    cd 世界模型
    streamlit run app.py --server.headless true
) else if exist "world_model\app.py" (
    cd world_model
    streamlit run app.py --server.headless true
) else (
    echo 找不到 app.py，請確認世界模型目錄存在
    pause
)
