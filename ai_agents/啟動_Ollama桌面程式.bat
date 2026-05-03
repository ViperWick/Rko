@echo off
chcp 65001 >nul
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\Ollama.exe"
if exist "%OLLAMA_EXE%" (
  start "" "%OLLAMA_EXE%"
  echo 已啟動 Ollama 桌面程式。
) else (
  echo 找不到：%OLLAMA_EXE%
  echo 請從「開始」選單手動開啟 Ollama。
)
pause
