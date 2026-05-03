# Open weekly macro/energy Canvas in Cursor (.canvas.tsx lives under %USERPROFILE%\.cursor\projects\*\canvases\)
# Double-click open_weekly_canvas.bat, or run the VS Code task "Open: 每週宏觀能源 Canvas".

$ErrorActionPreference = "Stop"
$targetName = "weekly-macro-energy-check.canvas.tsx"
$root = Join-Path $env:USERPROFILE ".cursor\projects"
if (-not (Test-Path $root)) {
    Write-Host "Missing Cursor projects folder: $root" -ForegroundColor Red
    exit 1
}

$canvas = Get-ChildItem -Path $root -Recurse -Filter $targetName -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Directory.Name -eq "canvases" } |
    Select-Object -First 1

if (-not $canvas) {
    Write-Host "Could not find $targetName under ...\canvases\" -ForegroundColor Red
    exit 1
}

$exe = Join-Path $env:LOCALAPPDATA "Programs\cursor\Cursor.exe"
if (-not (Test-Path $exe)) {
    $alt = Join-Path $env:LOCALAPPDATA "Programs\Cursor\Cursor.exe"
    if (Test-Path $alt) { $exe = $alt }
}

if (Test-Path $exe) {
    Start-Process -FilePath $exe -ArgumentList $canvas.FullName
    Write-Host "Opened in Cursor: $($canvas.FullName)"
    exit 0
}

$cursorCmd = Get-Command cursor -ErrorAction SilentlyContinue
if ($cursorCmd) {
    Start-Process -FilePath "cursor" -ArgumentList $canvas.FullName
    Write-Host "Opened via cursor CLI: $($canvas.FullName)"
    exit 0
}

Write-Host "Cursor.exe and 'cursor' CLI not found. Install Shell Command from Cursor menu." -ForegroundColor Red
exit 1
