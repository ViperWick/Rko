@echo off
chcp 65001 >nul
REM 創造者系統 — 一鍵收納發現文檔（掃描 發現文檔收納 並更新 發現文檔索引.md）
cd /d "%~dp0"

echo 正在安裝依賴（若尚未安裝）...
pip install -q -r requirements_收納.txt 2>nul

echo.
echo 執行收納腳本...
python 收納發現文檔.py

echo.
pause
