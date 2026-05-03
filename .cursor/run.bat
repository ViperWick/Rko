@echo off
chcp 65001 >nul
cd /d "%~dp0" 
"C:\Users\User\anaconda3\python.exe" run_world_model.py
if errorlevel 1 pause
