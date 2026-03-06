$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$RunDir = Join-Path $ProjectRoot ".run"

function Write-Info {
    param([string]$Message)
    Write-Host "[ClipAI] $Message"
}

function Stop-PidFileProcess {
    param([string]$PidFile, [string]$Name)

    if (-not (Test-Path $PidFile)) {
        return
    }

    $pidRaw = (Get-Content $PidFile -Raw).Trim()
    if (-not $pidRaw) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return
    }

    try {
        $procId = [int]$pidRaw
        Stop-Process -Id $procId -Force -ErrorAction Stop
        Write-Info "$Name arrete (PID $procId)."
    }
    catch {
        Write-Info "$Name deja arrete ou PID invalide ($pidRaw)."
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Stop-PortListeners {
    param([int]$Port)
    try {
        $procIds = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique
    }
    catch {
        $procIds = @()
    }

    foreach ($procId in $procIds) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Info "Port $Port libere (PID $procId arrete)."
        }
        catch {
            Write-Info "Impossible d'arreter PID $procId sur port $Port."
        }
    }
}

Stop-PidFileProcess -PidFile (Join-Path $RunDir "backend.pid") -Name "Backend"
Stop-PidFileProcess -PidFile (Join-Path $RunDir "frontend.pid") -Name "Frontend"
Stop-PortListeners -Port 8000
Stop-PortListeners -Port 5173

Write-Info "Services ClipAI arretes."
