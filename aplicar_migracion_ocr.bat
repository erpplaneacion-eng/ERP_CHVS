@echo off
echo ========================================
echo   Aplicando Migracion OCR Validation
echo ========================================
echo.

cd erp_chvs

echo [1/2] Aplicando migracion...
python manage.py migrate ocr_validation
echo.

echo [2/2] Verificando migracion...
python manage.py showmigrations ocr_validation
echo.

echo ========================================
echo   Migracion Completada
echo ========================================
echo.
pause
