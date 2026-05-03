# World Model - Add Anaconda to PATH
$anaconda = "C:\Users\User\anaconda3"
$pathsToAdd = @(
    $anaconda,
    "$anaconda\Scripts",
    "$anaconda\Library\bin"
)

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$alreadyAdded = $pathsToAdd | Where-Object { $currentPath -like "*$_*" }

if ($alreadyAdded.Count -eq 0) {
    $newPath = $currentPath + ";" + ($pathsToAdd -join ";")
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Anaconda added to PATH" -ForegroundColor Green
} else {
    Write-Host "Anaconda already in PATH" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Installing numpy, matplotlib..." -ForegroundColor Cyan
& "$anaconda\python.exe" -m pip install numpy matplotlib -q
Write-Host "Done. Restart terminal to use conda/python." -ForegroundColor Green
