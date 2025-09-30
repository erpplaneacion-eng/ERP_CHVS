@echo off
echo 🚀 Instalando dependencias para Sistema OCR en Windows
echo ===================================================

echo.
echo 📋 Verificando Python...
python --version
if errorlevel 1 (
    echo ❌ Python no encontrado. Instale Python desde https://python.org
    pause
    exit /b 1
)

echo.
echo 📦 Instalando dependencias Python...
pip install -r ocr_validation/requirements.txt

if errorlevel 1 (
    echo ❌ Error instalando dependencias Python
    echo 💡 Asegúrese de tener activado el entorno virtual
    pause
    exit /b 1
)

echo.
echo ✅ Dependencias Python instaladas correctamente

echo.
echo 📋 Próximos pasos:
echo 1. Ejecute: python manage.py makemigrations ocr_validation
echo 2. Ejecute: python manage.py migrate
echo 3. Ejecute: python verificar_sistema.py
echo 4. Acceda al sistema desde el dashboard de facturación

echo.
echo 🎯 El sistema OCR está listo para usar!
pause