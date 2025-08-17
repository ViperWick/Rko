@echo off
echo 正在啟動Jupyter Notebook...
echo.

cd /d "C:\Users\User\.cursor-tutor"
echo 進入工作目錄: %CD%

echo 激活虛擬環境...
call .venv\Scripts\activate.bat

echo 啟動Jupyter Notebook...
jupyter notebook

pause
