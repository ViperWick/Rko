#Requires -Version 5.1
<#
.SYNOPSIS
  Run eToro daily scripts in sequence, log to data/automation_logs.
  Use with Windows Task Scheduler.

.PARAMETER DryRun
  List steps only, do not run.

.PARAMETER StopOnError
  Stop remaining steps if one fails.
#>
param(
    [switch]$DryRun,
    [switch]$StopOnError
)

$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"

# This file lives in etoro_trading/scripts/
$ScriptDir = $PSScriptRoot
$EtoroRoot = Resolve-Path (Join-Path $ScriptDir "..")
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

$LogDir = Join-Path $EtoroRoot "data\automation_logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }
$LogFile = Join-Path $LogDir ("daily_{0:yyyyMMdd_HHmmss}.log" -f (Get-Date))

function Write-Log {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
    Write-Host $line
}

# Edit this list: comment out steps you do not need
$Steps = @(
    @{ Name = "export-portfolio";    Args = @("-m", "etoro_trading.scripts", "export-portfolio") }
    @{ Name = "daily-performance";   Args = @("-m", "etoro_trading.scripts", "daily-performance") }
    @{ Name = "today-summary";     Args = @("-m", "etoro_trading.scripts", "today-summary") }
    @{ Name = "check-yesterday";   Args = @("-m", "etoro_trading.scripts", "check-yesterday") }
)

Write-Log "===== START daily automation RepoRoot=$RepoRoot ====="
if ($DryRun) { Write-Log "[DryRun] preview only" }

Set-Location -LiteralPath $RepoRoot

$py = "py"
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    $py = "python"
}

$failed = $false
foreach ($step in $Steps) {
    $name = $step.Name
    Write-Log ">>> START $name"
    if ($DryRun) {
        Write-Log "    $py $($step.Args -join ' ')"
        continue
    }
    try {
        $out = & $py @($step.Args) 2>&1
        $code = $LASTEXITCODE
        foreach ($line in @($out)) {
            Write-Log ("    " + $line)
        }
        if ($null -ne $code -and $code -ne 0) {
            Write-Log "!!! FAIL $name exit=$code"
            $failed = $true
            if ($StopOnError) { break }
        }
        else {
            Write-Log ">>> OK $name"
        }
    }
    catch {
        Write-Log "!!! EXCEPTION $name : $_"
        $failed = $true
        if ($StopOnError) { break }
    }
}

Write-Log "===== END failed=$failed LogFile=$LogFile ====="
if ($failed -and $StopOnError) { exit 1 }
exit 0
