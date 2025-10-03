# Script PowerShell para crear y aplicar migraciones del módulo de nutrición
# Ejecutar desde: C:\Users\User\OneDrive\Desktop\CHVS\ERP_CHVS

Write-Host "========================================"
Write-Host "MIGRACIONES MODULO DE NUTRICION"
Write-Host "========================================"
Write-Host ""

# Activar entorno virtual
Write-Host "[1/4] Activando entorno virtual..." -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"
Write-Host "OK - Entorno virtual activado" -ForegroundColor Green
Write-Host ""

# Cambiar al directorio erp_chvs
Set-Location -Path ".\erp_chvs"

# Crear las migraciones
Write-Host "[2/4] Creando migraciones..." -ForegroundColor Cyan
python manage.py makemigrations nutricion
Write-Host ""

# Aplicar las migraciones
Write-Host "[3/4] Aplicando migraciones..." -ForegroundColor Cyan
python manage.py migrate nutricion
Write-Host ""

# Verificar modelos
Write-Host "[4/4] Verificando modelos..." -ForegroundColor Cyan
python manage.py check
Write-Host ""

Write-Host "========================================"
Write-Host "PROCESO COMPLETADO" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "Ahora puedes acceder a:" -ForegroundColor Yellow
Write-Host "- http://localhost:8000/nutricion/menus/"
Write-Host "- http://localhost:8000/nutricion/preparaciones/"
Write-Host "- http://localhost:8000/nutricion/ingredientes/"
Write-Host ""

Read-Host "Presiona Enter para salir"
