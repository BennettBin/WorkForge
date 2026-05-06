$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pidFile = Join-Path $workspaceRoot "storage\logs\backend.pid"

if (-not (Test-Path $pidFile)) {
    Write-Output "No backend pid file found."
    exit 0
}

$pidText = Get-Content $pidFile -Raw
$targetPid = 0
[void][int]::TryParse($pidText, [ref]$targetPid)

if ($targetPid -gt 0) {
    $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $targetPid -Force
        Write-Output "Stopped backend PID $targetPid"
    }
}

if (Test-Path $pidFile) {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}

# Fallback: if another backend instance is listening on 8080, stop it as well.
$existing = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    $existingPid = $existing.OwningProcess | Select-Object -First 1
    if ($existingPid -and $existingPid -gt 0) {
        $proc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $existingPid -Force
            Write-Output "Stopped process on port 8080 PID $existingPid"
        }
    }
}
