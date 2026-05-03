@echo off
chcp 65001 >nul
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\anaconda3;%PATH%"
cd /d "%~dp0\..\.."
echo 正在啟動 eToro 交易程式 — 簡易展示（不需 API 金鑰）...
py -m streamlit run etoro_trading/ui/app_ui_demo.py
pause
