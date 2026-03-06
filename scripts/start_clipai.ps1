param(
    [switch]$ForceRestart,
    [switch]$NoInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$RunDir = Join-Path $ProjectRoot ".run"
$LogsDir = Join-Path $ProjectRoot "logs"

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

function Write-Info {
    param([string]$Message)
    Write-Host "[ClipAI] $Message"
}

function Get-ListeningPids {
    param([int]$Port)
    try {
        return Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique
    }
    catch {
        return @()
    }
}

function Stop-PortListeners {
    param([int]$Port)
    $procIds = Get-ListeningPids -Port $Port
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

function Wait-HttpReady {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 40
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            if ($Url -like "*/health") {
                $resp = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 2
                if ($resp.status -eq "ok") {
                    return $true
                }
            }
            else {
                $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
                if ($resp.StatusCode -eq 200) {
                    return $true
                }
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    return $false
}

function Test-R2ConfigPresent {
    param([string]$EnvPath)
    if (-not (Test-Path $EnvPath)) {
        return $false
    }

    $required = @(
        "CLOUDFLARE_R2_ACCESS_KEY",
        "CLOUDFLARE_R2_SECRET_KEY",
        "CLOUDFLARE_R2_BUCKET",
        "CLOUDFLARE_R2_ENDPOINT"
    )

    $lines = Get-Content $EnvPath
    foreach ($key in $required) {
        $match = $lines | Where-Object { $_ -like "$key=*" } | Select-Object -First 1
        if (-not $match) {
            return $false
        }
        $value = ($match -split "=", 2)[1].Trim()
        if (-not $value) {
            return $false
        }
    }
    return $true
}

if ($ForceRestart) {
    Stop-PortListeners -Port 8000
    Stop-PortListeners -Port 5173
}

$backendPy = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $backendPy)) {
    Write-Info "Creation de l'environnement virtuel backend..."
    python -m venv (Join-Path $BackendDir ".venv")
}

if (-not (Test-Path $backendPy)) {
    throw "Python venv backend introuvable apres creation."
}

if (-not $NoInstall) {
    $requirementsFile = Join-Path $BackendDir "requirements.txt"
    $backendHashFile = Join-Path $RunDir "backend_requirements.sha256"
    $currentBackendHash = (Get-FileHash -Path $requirementsFile -Algorithm SHA256).Hash
    $savedBackendHash = if (Test-Path $backendHashFile) { (Get-Content $backendHashFile -Raw).Trim() } else { "" }

    if ($currentBackendHash -ne $savedBackendHash) {
        Write-Info "Installation/maj des dependances backend..."
        & $backendPy -m pip install --upgrade pip
        & $backendPy -m pip install -r $requirementsFile
        $currentBackendHash | Set-Content -Encoding ASCII $backendHashFile
    }

    $packageFile = Join-Path $FrontendDir "package.json"
    $frontendHashFile = Join-Path $RunDir "frontend_package.sha256"
    $nodeModulesDir = Join-Path $FrontendDir "node_modules"
    $currentFrontendHash = (Get-FileHash -Path $packageFile -Algorithm SHA256).Hash
    $savedFrontendHash = if (Test-Path $frontendHashFile) { (Get-Content $frontendHashFile -Raw).Trim() } else { "" }

    if ((-not (Test-Path $nodeModulesDir)) -or ($currentFrontendHash -ne $savedFrontendHash)) {
        Write-Info "Installation/maj des dependances frontend..."
        Push-Location $FrontendDir
        try {
            npm install
        }
        finally {
            Pop-Location
        }
        $currentFrontendHash | Set-Content -Encoding ASCII $frontendHashFile
    }
}

if ((Get-ListeningPids -Port 8000).Count -eq 0) {
    $backendOutLog = Join-Path $LogsDir "backend.out.log"
    $backendErrLog = Join-Path $LogsDir "backend.err.log"
    $backendProc = Start-Process -FilePath $backendPy -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $BackendDir -RedirectStandardOutput $backendOutLog -RedirectStandardError $backendErrLog -PassThru
    $backendPidFile = Join-Path $RunDir "backend.pid"
    $backendProc.Id | Set-Content -Encoding ASCII $backendPidFile
    Write-Info "Backend demarre (PID $($backendProc.Id))."
}
else {
    Write-Info "Backend deja actif sur 8000."
}

if ((Get-ListeningPids -Port 5173).Count -eq 0) {
    $frontendOutLog = Join-Path $LogsDir "frontend.out.log"
    $frontendErrLog = Join-Path $LogsDir "frontend.err.log"
    $frontendProc = Start-Process -FilePath "npm.cmd" -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5173") -WorkingDirectory $FrontendDir -RedirectStandardOutput $frontendOutLog -RedirectStandardError $frontendErrLog -PassThru
    $frontendPidFile = Join-Path $RunDir "frontend.pid"
    $frontendProc.Id | Set-Content -Encoding ASCII $frontendPidFile
    Write-Info "Frontend demarre (PID $($frontendProc.Id))."
}
else {
    Write-Info "Frontend deja actif sur 5173."
}

if (-not (Wait-HttpReady -Url "http://127.0.0.1:8000/health" -TimeoutSeconds 45)) {
    throw "Backend indisponible sur http://127.0.0.1:8000/health"
}

if (-not (Wait-HttpReady -Url "http://127.0.0.1:5173" -TimeoutSeconds 60)) {
    throw "Frontend indisponible sur http://127.0.0.1:5173"
}

Write-Info "Stack ClipAI operationnelle."
Write-Host "Backend : http://127.0.0.1:8000"
Write-Host "Frontend: http://127.0.0.1:5173"

$envFile = Join-Path $BackendDir ".env"
if (Test-R2ConfigPresent -EnvPath $envFile) {
    Write-Info "Cloudflare R2 configure: upload distant actif."
}
else {
    Write-Info "Cloudflare R2 non configure: fallback local /media actif."
}

