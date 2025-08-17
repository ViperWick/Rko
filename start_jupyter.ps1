# Jupyter Notebook 一鍵啟動腳本
Write-Host "🚀 正在啟動Jupyter Notebook..." -ForegroundColor Green
Write-Host ""

# 進入工作目錄
Set-Location "C:\Users\User\.cursor-tutor"
Write-Host "📁 進入工作目錄: $(Get-Location)" -ForegroundColor Blue

# 激活虛擬環境
Write-Host "🔧 激活虛擬環境..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# 啟動Jupyter
Write-Host "🌟 啟動Jupyter Notebook..." -ForegroundColor Green
jupyter notebook
