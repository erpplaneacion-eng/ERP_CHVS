@echo off
echo 🚀 Guía de Configuración del Sistema OCR
echo =======================================
echo.

echo 📋 PASO 1: Buscar Tesseract automáticamente
echo.
python buscar_tesseract.py

echo.
echo 📋 PASO 2: Si no se encontró Tesseract automáticamente
echo.
echo 💡 OPCIONES PARA CONFIGURAR TESSERACT:
echo.
echo OPCION A - Usar configuración automática:
echo   1. Ejecute: python configurar_tesseract.py
echo   2. Esto creará un archivo de configuración
echo.
echo OPCION B - Configuración manual:
echo   1. Busque tesseract.exe en el Explorador de Windows
echo   2. Anote la ruta completa (ej: C:\Program Files\Tesseract-OCR\tesseract.exe)
echo   3. Modifique la línea 47 en ocr_validation/ocr_service.py
echo   4. Reemplace la ruta por defecto con la ruta correcta
echo.
echo OPCION C - Agregar al PATH del sistema:
echo   1. Presione Win + R
echo   2. Escriba: sysdm.cpl
echo   3. Variables de entorno - Path - Editar - Nuevo
echo   4. Agregue la carpeta que contiene tesseract.exe
echo   5. Reinicie la computadora
echo.

echo 📋 PASO 3: Verificar instalación completa
echo.
echo Después de configurar Tesseract, ejecute:
echo   python verificar_sistema.py
echo.

echo 📋 PASO 4: Crear tablas de base de datos
echo.
echo Cuando Tesseract esté funcionando, ejecute:
echo   python manage.py makemigrations ocr_validation
echo   python manage.py migrate
echo.

echo 🎯 El sistema estará listo para usar después de estos pasos.
echo.
pause