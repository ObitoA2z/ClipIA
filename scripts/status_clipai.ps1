$ErrorActionPreference = "Stop"

function Get-PortStatus {
    param([int]$Port)

    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        return $conn.OwningProcess
    }
    catch {
        return $null
    }
}

$backendPid = Get-PortStatus -Port 8000
$frontendPid = Get-PortStatus -Port 5173

$backendHealth = $false
$frontendHealth = $false

try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 2
    if ($resp.status -eq "ok") {
        $backendHealth = $true
    }
}
catch {}

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -UseBasicParsing -TimeoutSec 2
    if ($resp.StatusCode -eq 200) {
        $frontendHealth = $true
    }
}
catch {}

$backendPidDisplay = if ($null -ne $backendPid) { $backendPid } else { "offline" }
$frontendPidDisplay = if ($null -ne $frontendPid) { $frontendPid } else { "offline" }

Write-Host "Backend PID :" $backendPidDisplay
Write-Host "Backend OK  :" $backendHealth
Write-Host "Frontend PID:" $frontendPidDisplay
Write-Host "Frontend OK :" $frontendHealth
