$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pidFile = Join-Path $workspaceRoot "storage\logs\backend.pid"

function Stop-IfRunning {
    param(
        [int]$ProcessId
    )
    if ($ProcessId -le 0) {
        return $false
    }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) {
        return $false
    }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    Write-Output "Stopped PID $ProcessId"
    return $true
}

$stoppedAny = $false

# 1) Stop pid from pid-file if present.
if (Test-Path $pidFile) {
    $pidText = Get-Content $pidFile -Raw
    $targetPid = 0
    [void][int]::TryParse($pidText, [ref]$targetPid)
    if (Stop-IfRunning -ProcessId $targetPid) {
        $stoppedAny = $true
    }
} else {
    Write-Output "No backend pid file found."
}

# 2) Stop listeners on backend port.
$listeners = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($listeners) {
    $listenerPids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $listenerPids) {
        if (Stop-IfRunning -ProcessId ([int]$procId)) {
            $stoppedAny = $true
        }
    }
}

# 3) Kill any uvicorn process for this backend command line, even if port probe misses it.
$uvicornProcs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        ($_.Name -ieq "python.exe" -or $_.Name -ieq "pythonw.exe") -and
        $_.CommandLine -and
        $_.CommandLine -match "uvicorn" -and
        $_.CommandLine -match "app\.api\.app:app" -and
        $_.CommandLine -match "--port\s+8080"
    }
foreach ($proc in $uvicornProcs) {
    if (Stop-IfRunning -ProcessId ([int]$proc.ProcessId)) {
        $stoppedAny = $true
    }
}

# Remove pid file last.
if (Test-Path $pidFile) {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}

if (-not $stoppedAny) {
    Write-Output "No running backend process found."
}
