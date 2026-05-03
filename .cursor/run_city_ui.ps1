# 世界模型 - 統一城市 UI 啟動腳本
# 執行: powershell -ExecutionPolicy Bypass -File run_city_ui.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$appPath = Join-Path $scriptDir "世界模型\app.py"
if (-not (Test-Path $appPath)) {
    $appPath = Join-Path $scriptDir "world_model\app.py"
}

if (Test-Path $appPath) {
    Set-Location (Split-Path $appPath)
    Write-Host "啟動統一城市 UI..."
    streamlit run app.py --server.headless true
} else {
    Write-Host "找不到 app.py"
}
