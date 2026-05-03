@echo off
chcp 65001 >nul
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\miniconda3;%PATH%"
cd /d "%~dp0\..\.."
set "OUT=%CD%\etoro_trading\data\portfolio_output.txt"
py -m etoro_trading portfolio > "%OUT%" 2>&1
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "if ((Get-Item -LiteralPath '%OUT%' -ErrorAction SilentlyContinue).Length -lt 10) { Set-Content -LiteralPath '%OUT%' -Value '無法取得組合。請從 Cursor 終端執行: cd %CD% ; py -m etoro_trading portfolio' -Encoding UTF8 }"
echo [OK] 結果已寫入 %OUT%
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "Get-Content -LiteralPath '%OUT%' -Head 50 -Encoding UTF8 -ErrorAction SilentlyContinue"
echo.
start notepad "%OUT%"
pause

