$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendDir = Join-Path $workspaceRoot "backend"
$logDir = Join-Path $workspaceRoot "storage\logs"
$pidFile = Join-Path $logDir "backend.pid"
$outFile = Join-Path $logDir "backend.out.log"
$errFile = Join-Path $logDir "backend.err.log"

New-Item -ItemType Directory -Path $logDir -Force | Out-Null

# Ensure target port is free; otherwise we may hit an old backend process.
$existing = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    $existingPid = $existing.OwningProcess | Select-Object -First 1
    if ($existingPid -and $existingPid -gt 0) {
        $proc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $existingPid -Force
            Write-Output "Stopped existing process on port 8080 (PID $existingPid)."
            Start-Sleep -Milliseconds 300
        }
    }
}

if (Test-Path $pidFile) {
    $pidText = Get-Content -Path $pidFile -Raw
    $targetPid = 0
    [void][int]::TryParse($pidText, [ref]$targetPid)
    if ($targetPid -gt 0) {
        $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Output "Backend already running with PID $targetPid"
            exit 0
        }
    }
    Remove-Item -LiteralPath $pidFile -Force
    Write-Output "Removed stale backend pid file."
}

$process = Start-Process `
  -FilePath "python" `
  -ArgumentList "-m", "uvicorn", "app.api.app:app", "--host", "127.0.0.1", "--port", "8080" `
  -WorkingDirectory $backendDir `
  -RedirectStandardOutput $outFile `
  -RedirectStandardError $errFile `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $pidFile -Value $process.Id -Encoding ascii

$healthUrl = "http://127.0.0.1:8080/WorkForge"
$started = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 300
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            $started = $true
            break
        }
    } catch {
        # wait until backend is ready
    }
}

if (-not $started) {
    $proc = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $process.Id -Force
    }
    if (Test-Path $pidFile) {
        Remove-Item -LiteralPath $pidFile -Force
    }
    throw "Backend failed to become ready at $healthUrl"
}

Write-Output "Backend started with PID $($process.Id) and health check passed."
