@echo off
echo ==========================================
echo EJECUTANDO TESTS - PASO 1
echo Sincronizacion de Gramajes
echo ==========================================
echo.

REM Activar virtualenv si existe
if exist "..\venv\Scripts\activate.bat" (
    echo Activando virtualenv...
    call ..\venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activando virtualenv...
    call .venv\Scripts\activate.bat
)

REM Ejecutar tests
echo Ejecutando tests con Django...
python manage.py test nutricion.tests_sincronizacion_pesos --verbosity=2

echo.
echo ==========================================
if %ERRORLEVEL% EQU 0 (
    echo TODOS LOS TESTS PASARON
) else (
    echo ALGUNOS TESTS FALLARON
)
echo ==========================================

pause
