$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendEnv = Join-Path $ProjectRoot "backend\.env"

function Write-Info {
    param([string]$Message)
    Write-Host "[ClipAI:R2] $Message"
}

function Get-EnvValue {
    param([string]$Path, [string]$Name)
    if (-not (Test-Path $Path)) {
        return ""
    }
    $line = Get-Content $Path | Where-Object { $_ -like "$Name=*" } | Select-Object -First 1
    if (-not $line) {
        return ""
    }
    return ($line -split "=", 2)[1].Trim()
}

$required = @(
    "CLOUDFLARE_R2_ACCESS_KEY",
    "CLOUDFLARE_R2_SECRET_KEY",
    "CLOUDFLARE_R2_BUCKET",
    "CLOUDFLARE_R2_ENDPOINT"
)

$missing = @()
foreach ($name in $required) {
    $value = Get-EnvValue -Path $BackendEnv -Name $name
    if (-not $value) {
        $missing += $name
    }
}

if ($missing.Count -gt 0) {
    Write-Info "Configuration R2 incomplete. Variables manquantes:" 
    foreach ($name in $missing) {
        Write-Host " - $name"
    }
    exit 1
}

if (-not (Test-Path "$ProjectRoot\backend\.venv\Scripts\python.exe")) {
    Write-Info "Environnement Python backend absent. Lance start_clipai.ps1 d'abord."
    exit 1
}

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 5
    if ($health.status -ne "ok") {
        throw "Backend unhealthy"
    }
}
catch {
    Write-Info "Backend indisponible sur 127.0.0.1:8000. Lance start_clipai.ps1."
    exit 1
}

$email = "r2test_$(Get-Random -Minimum 100000 -Maximum 999999)@example.com"
$password = "Pass1234"

$registerBody = @{ email = $email; password = $password; full_name = "R2 Tester" } | ConvertTo-Json
$null = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/register" -Method Post -ContentType "application/json" -Body $registerBody

$loginBody = @{ email = $email; password = $password } | ConvertTo-Json
$login = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login" -Method Post -ContentType "application/json" -Body $loginBody

$videoBody = @{ youtube_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" } | ConvertTo-Json
$video = Invoke-RestMethod -Uri "http://127.0.0.1:8000/video/process" -Method Post -ContentType "application/json" -Body $videoBody
$videoId = $video.id

$status = $null
for ($i = 0; $i -lt 240; $i++) {
    Start-Sleep -Seconds 1
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:8000/video/$videoId/status" -Method Get
    if ($status.status -eq "done" -or $status.status -eq "error") {
        break
    }
}

if (-not $status -or $status.status -ne "done") {
    Write-Info "Pipeline non finalisee en mode done. Statut final: $($status.status)"
    exit 1
}

$clips = Invoke-RestMethod -Uri "http://127.0.0.1:8000/clips/$videoId" -Method Get
if (-not $clips -or $clips.Count -lt 1) {
    Write-Info "Aucun clip genere."
    exit 1
}

$first = $clips[0]
$fileUrl = [string]$first.file_url

if ($fileUrl -like "http://127.0.0.1:8000/media/*" -or $fileUrl -like "http://localhost:8000/media/*") {
    Write-Info "Upload R2 non actif: URL locale detectee ($fileUrl)"
    exit 1
}

try {
    $probe = Invoke-WebRequest -Uri $fileUrl -UseBasicParsing -Method Get -TimeoutSec 20
    if ($probe.StatusCode -lt 200 -or $probe.StatusCode -ge 400) {
        throw "HTTP $($probe.StatusCode)"
    }
}
catch {
    Write-Info "URL clip R2 generee mais non lisible immediatement: $fileUrl"
    Write-Info "Verifier policy publique ou URL signee R2."
    exit 1
}

Write-Info "R2 actif et valide."
Write-Host "Video ID : $videoId"
Write-Host "Clip URL : $fileUrl"
exit 0
