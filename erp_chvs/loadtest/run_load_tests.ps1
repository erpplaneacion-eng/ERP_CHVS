param(
    [Parameter(Mandatory = $false)]
    [string]$HostUrl = "http://localhost:8000",

    [Parameter(Mandatory = $false)]
    [string]$OutDir = "loadtest\reports",

    [Parameter(Mandatory = $false)]
    [int]$SpawnRate = 5
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

$PythonExe = "..\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    throw "No se encontró Python de entorno virtual en $PythonExe"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runDir = Join-Path $OutDir $timestamp
New-Item -ItemType Directory -Path $runDir | Out-Null

function Invoke-LocustRun {
    param(
        [string]$Name,
        [int]$Users,
        [string]$RunTime,
        [string]$Tags,
        [string]$Suite
    )

    $html = Join-Path $runDir "$Name.html"
    $csv = Join-Path $runDir "$Name"

    Write-Host "==> Ejecutando $Name (users=$Users, runtime=$RunTime, tags=$Tags)"
    $env:LT_SUITE = $Suite
    & $PythonExe -m locust `
        -f loadtest/locustfile.py `
        --headless `
        --host $HostUrl `
        -u $Users `
        -r $SpawnRate `
        --run-time $RunTime `
        --tags $Tags `
        --html $html `
        --csv $csv
}

Write-Host "Directorio de salida: $runDir"
Write-Host "Host: $HostUrl"

# Baseline core (subida progresiva)
Invoke-LocustRun -Name "baseline-core-u05" -Users 5  -RunTime "3m"  -Tags "core" -Suite "core"
Invoke-LocustRun -Name "baseline-core-u10" -Users 10 -RunTime "3m"  -Tags "core" -Suite "core"
Invoke-LocustRun -Name "baseline-core-u20" -Users 20 -RunTime "4m"  -Tags "core" -Suite "core"
Invoke-LocustRun -Name "baseline-core-u30" -Users 30 -RunTime "5m"  -Tags "core" -Suite "core"

# Stress corto
Invoke-LocustRun -Name "stress-core-u40"   -Users 40 -RunTime "4m"  -Tags "core" -Suite "core"
Invoke-LocustRun -Name "stress-core-u50"   -Users 50 -RunTime "4m"  -Tags "core" -Suite "core"

# Heavy (PDF/ZIP)
Invoke-LocustRun -Name "heavy-u03"         -Users 3  -RunTime "6m"  -Tags "heavy" -Suite "heavy"

# IA (NIA/Gemini)
Invoke-LocustRun -Name "ia-u05"            -Users 5  -RunTime "5m"  -Tags "ia" -Suite "ia"

# Soak
Invoke-LocustRun -Name "soak-core-u30"     -Users 30 -RunTime "20m" -Tags "core" -Suite "core"

Write-Host "Listo. Reportes generados en: $runDir"
