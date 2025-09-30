#!/usr/bin/env python3
"""
Script de prueba para verificar el endpoint de procesamiento OCR
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✅ Django configurado correctamente")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("VERIFICACIÓN DEL ENDPOINT OCR")
print("="*60)

# 1. Verificar que la app está registrada
print("\n1. Verificando app ocr_validation...")
from django.conf import settings
if 'ocr_validation' in settings.INSTALLED_APPS:
    print("   ✅ ocr_validation está en INSTALLED_APPS")
else:
    print("   ❌ ocr_validation NO está en INSTALLED_APPS")
    sys.exit(1)

# 2. Verificar URLs
print("\n2. Verificando URLs...")
try:
    from django.urls import reverse, resolve

    # Verificar URL del index
    index_url = reverse('ocr_validation:ocr_index')
    print(f"   ✅ URL index: {index_url}")

    # Verificar URL de procesamiento
    procesar_url = reverse('ocr_validation:procesar_pdf')
    print(f"   ✅ URL procesar: {procesar_url}")

    # Verificar que la vista existe
    match = resolve(procesar_url)
    print(f"   ✅ Vista: {match.view_name} -> {match.func.__name__}")

except Exception as e:
    print(f"   ❌ Error verificando URLs: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Verificar modelos
print("\n3. Verificando modelos...")
try:
    from ocr_validation.models import PDFValidation, ValidationError, OCRConfiguration

    # Verificar tablas en BD (compatible con PostgreSQL y SQLite)
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            # Detectar tipo de base de datos
            db_engine = settings.DATABASES['default']['ENGINE']

            if 'sqlite' in db_engine:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ocr_%';")
                tablas = cursor.fetchall()
            elif 'postgresql' in db_engine:
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'ocr_%';")
                tablas = cursor.fetchall()
            else:
                cursor.execute("SHOW TABLES LIKE 'ocr_%';")
                tablas = cursor.fetchall()

            if tablas:
                print(f"   ✅ Tablas encontradas: {[t[0] for t in tablas]}")
            else:
                print("   ⚠️  No se encontraron tablas OCR. Ejecutar: python manage.py migrate")
    except Exception as e:
        print(f"   ⚠️  No se pudo verificar tablas: {e}")

    # Verificar si existe configuración OCR
    config_count = OCRConfiguration.objects.count()
    if config_count > 0:
        print(f"   ✅ Configuración OCR existe ({config_count} registros)")
    else:
        print("   ⚠️  No existe configuración OCR. Creando una por defecto...")
        OCRConfiguration.objects.create()
        print("   ✅ Configuración OCR creada")

except Exception as e:
    print(f"   ❌ Error verificando modelos: {e}")
    import traceback
    traceback.print_exc()

# 4. Verificar dependencias OCR
print("\n4. Verificando dependencias OCR...")

# pytesseract
try:
    import pytesseract
    from PIL import Image
    print("   ✅ pytesseract y PIL instalados")
except ImportError as e:
    print(f"   ❌ pytesseract/PIL no disponibles: {e}")

# pdf2image
try:
    from pdf2image import convert_from_path
    print("   ✅ pdf2image instalado")
except ImportError as e:
    print(f"   ❌ pdf2image no disponible: {e}")

# PyPDF2
try:
    from PyPDF2 import PdfReader
    print("   ✅ PyPDF2 instalado")
except ImportError as e:
    print(f"   ❌ PyPDF2 no disponible: {e}")

# opencv
try:
    import cv2
    print("   ✅ opencv-python instalado")
except ImportError as e:
    print(f"   ⚠️  opencv-python no disponible: {e}")

# 5. Verificar Tesseract ejecutable
print("\n5. Verificando ejecutable Tesseract...")
import platform
if platform.system() == 'Windows':
    rutas_tesseract = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe',
    ]

    tesseract_encontrado = False
    for ruta in rutas_tesseract:
        if os.path.exists(ruta):
            print(f"   ✅ Tesseract: {ruta}")
            tesseract_encontrado = True
            break

    if not tesseract_encontrado:
        print("   ❌ Tesseract no encontrado en rutas estándar")
else:
    import subprocess
    try:
        result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Tesseract: {result.stdout.strip()}")
        else:
            print("   ❌ Tesseract no encontrado")
    except Exception as e:
        print(f"   ❌ Error verificando Tesseract: {e}")

# 6. Verificar Poppler
print("\n6. Verificando Poppler (requerido por pdf2image)...")
if platform.system() == 'Windows':
    rutas_poppler = [
        r'C:\Program Files\poppler\Library\bin',
        r'C:\poppler\Library\bin',
    ]

    poppler_encontrado = False
    for ruta in rutas_poppler:
        if os.path.exists(ruta):
            print(f"   ✅ Poppler: {ruta}")
            poppler_encontrado = True
            break

    if not poppler_encontrado:
        print("   ⚠️  Poppler no encontrado. pdf2image puede fallar")
else:
    try:
        result = subprocess.run(['which', 'pdftoppm'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Poppler encontrado")
        else:
            print("   ⚠️  Poppler no encontrado")
    except:
        print("   ⚠️  No se pudo verificar Poppler")

# 7. Probar importar el servicio OCR
print("\n7. Verificando servicio OCR...")
try:
    from ocr_validation.ocr_service import OCRProcessor, procesar_pdf_ocr_view
    print("   ✅ Servicio OCR importado correctamente")

    # Intentar crear instancia
    try:
        processor = OCRProcessor()
        print("   ✅ OCRProcessor instanciado correctamente")
    except Exception as e:
        print(f"   ❌ Error creando OCRProcessor: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"   ❌ Error importando servicio OCR: {e}")
    import traceback
    traceback.print_exc()

# 8. Verificar vista
print("\n8. Verificando vista procesar_pdf_ocr...")
try:
    from ocr_validation.views import procesar_pdf_ocr
    print(f"   ✅ Vista procesar_pdf_ocr importada: {procesar_pdf_ocr}")
except Exception as e:
    print(f"   ❌ Error importando vista: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("VERIFICACIÓN COMPLETADA")
print("="*60)

print("\n📋 RESUMEN:")
print("   - Endpoint esperado: /ocr_validation/procesar/")
print("   - Método: POST")
print("   - Parámetro: archivo_pdf (tipo file)")
print("   - CSRF Token: Requerido")
print("\n💡 SIGUIENTE PASO:")
print("   1. Ejecutar el servidor: python manage.py runserver")
print("   2. Abrir navegador en: http://localhost:8000/ocr_validation/")
print("   3. Abrir DevTools (F12) en la pestaña Console")
print("   4. Cargar un PDF y verificar errores en consola")
print("   5. Verificar terminal del servidor para ver logs")
