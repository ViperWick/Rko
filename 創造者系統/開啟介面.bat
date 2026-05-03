@echo off
chcp 65001 >nul
REM 創造者系統 — 開啟簡易 Web 介面
cd /d "%~dp0\.."
pip install -q streamlit 2>nul
streamlit run 創造者系統/創造者系統_ui.py
