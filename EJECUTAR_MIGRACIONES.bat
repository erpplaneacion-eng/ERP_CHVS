@echo off
REM Script para crear y aplicar migraciones del módulo de nutrición
REM Ejecutar desde: C:\Users\User\OneDrive\Desktop\CHVS\ERP_CHVS

echo ========================================
echo MIGRACIONES MODULO DE NUTRICION
echo ========================================
echo.

REM Activar entorno virtual
echo [1/4] Activando entorno virtual...
call .venv\Scripts\activate.bat
echo OK - Entorno virtual activado
echo.

REM Cambiar al directorio erp_chvs
cd erp_chvs

REM Crear las migraciones
echo [2/4] Creando migraciones...
python manage.py makemigrations nutricion
echo.

REM Aplicar las migraciones
echo [3/4] Aplicando migraciones...
python manage.py migrate nutricion
echo.

REM Verificar que las tablas se crearon
echo [4/4] Verificando tablas creadas...
python manage.py dbshell -c "\dt tabla_*"
echo.

echo ========================================
echo PROCESO COMPLETADO
echo ========================================
echo.
echo Ahora puedes acceder a:
echo - http://localhost:8000/nutricion/menus/
echo - http://localhost:8000/nutricion/preparaciones/
echo - http://localhost:8000/nutricion/ingredientes/
echo.

pause
