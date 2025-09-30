#!/usr/bin/env python
"""
Script para verificar que todas las dependencias OCR están instaladas.
"""

import sys

print("=" * 60)
print("VERIFICACIÓN DE DEPENDENCIAS OCR")
print("=" * 60)

dependencias_ok = True

# 1. Verificar pytesseract y PIL
print("\n1. Verificando pytesseract y PIL...")
try:
    import pytesseract
    from PIL import Image
    print("   ✅ pytesseract y PIL instalados")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    print("   Instalar: pip install pytesseract Pillow")
    dependencias_ok = False

# 2. Verificar pdf2image
print("\n2. Verificando pdf2image...")
try:
    from pdf2image import convert_from_path
    print("   ✅ pdf2image instalado")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    print("   Instalar: pip install pdf2image")
    dependencias_ok = False

# 3. Verificar PyPDF2
print("\n3. Verificando PyPDF2...")
try:
    from PyPDF2 import PdfReader
    print("   ✅ PyPDF2 instalado")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    print("   Instalar: pip install PyPDF2")
    dependencias_ok = False

# 4. Verificar opencv
print("\n4. Verificando opencv-python...")
try:
    import cv2
    print("   ✅ opencv-python instalado")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    print("   Instalar: pip install opencv-python")
    dependencias_ok = False

# 5. Verificar numpy
print("\n5. Verificando numpy...")
try:
    import numpy
    print("   ✅ numpy instalado")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    print("   Instalar: pip install numpy")
    dependencias_ok = False

# 6. Verificar pandas (opcional)
print("\n6. Verificando pandas (opcional)...")
try:
    import pandas
    print("   ✅ pandas instalado")
except ImportError:
    print("   ⚠️  pandas no instalado (opcional para reportes Excel)")
    print("   Instalar: pip install pandas openpyxl")

# 7. Verificar Tesseract ejecutable
print("\n7. Verificando ejecutable Tesseract...")
import platform
import os

if platform.system() == 'Windows':
    rutas_tesseract = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]

    tesseract_encontrado = False
    for ruta in rutas_tesseract:
        if os.path.exists(ruta):
            print(f"   ✅ Tesseract encontrado en: {ruta}")
            tesseract_encontrado = True
            break

    if not tesseract_encontrado:
        print("   ❌ Tesseract no encontrado")
        print("   Descargar: https://github.com/UB-Mannheim/tesseract/wiki")
        dependencias_ok = False
else:
    # Linux/Mac
    import subprocess
    try:
        result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Tesseract encontrado en: {result.stdout.strip()}")
        else:
            print("   ❌ Tesseract no encontrado")
            print("   Instalar: sudo apt-get install tesseract-ocr tesseract-ocr-spa")
            dependencias_ok = False
    except:
        print("   ❌ No se pudo verificar Tesseract")
        dependencias_ok = False

# 8. Verificar Poppler (para pdf2image)
print("\n8. Verificando Poppler (para pdf2image)...")
if platform.system() == 'Windows':
    rutas_poppler = [
        r'C:\Program Files\poppler\Library\bin',
        r'C:\poppler\Library\bin',
        r'C:\Program Files (x86)\poppler\Library\bin',
    ]

    poppler_encontrado = False
    for ruta in rutas_poppler:
        if os.path.exists(ruta):
            print(f"   ✅ Poppler encontrado en: {ruta}")
            poppler_encontrado = True
            break

    if not poppler_encontrado:
        print("   ⚠️  Poppler no encontrado en ubicaciones estándar")
        print("   Descargar: https://github.com/oschwartz10612/poppler-windows/releases")
        print("   Nota: pdf2image puede fallar sin Poppler")
else:
    try:
        result = subprocess.run(['which', 'pdftoppm'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Poppler encontrado")
        else:
            print("   ❌ Poppler no encontrado")
            print("   Instalar: sudo apt-get install poppler-utils")
            dependencias_ok = False
    except:
        print("   ❌ No se pudo verificar Poppler")
        dependencias_ok = False

# 9. Verificar Django y app registrada
print("\n9. Verificando configuración Django...")
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
    django.setup()

    from django.conf import settings
    if 'ocr_validation' in settings.INSTALLED_APPS:
        print("   ✅ ocr_validation registrada en INSTALLED_APPS")
    else:
        print("   ❌ ocr_validation NO está en INSTALLED_APPS")
        dependencias_ok = False
except Exception as e:
    print(f"   ⚠️  No se pudo verificar Django: {e}")

# 10. Verificar migraciones
print("\n10. Verificando migraciones...")
try:
    from django.core.management import execute_from_command_line
    from io import StringIO
    import sys

    # Capturar salida
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    from django.core.management import call_command
    call_command('showmigrations', 'ocr_validation', '--plan')

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    if 'ocr_validation' in output and '[X]' in output:
        print("   ✅ Migraciones de ocr_validation aplicadas")
    elif 'ocr_validation' in output:
        print("   ⚠️  Migraciones pendientes. Ejecutar: python manage.py migrate")
    else:
        print("   ❌ No se encontraron migraciones de ocr_validation")
        dependencias_ok = False
except Exception as e:
    print(f"   ⚠️  No se pudo verificar migraciones: {e}")

print("\n" + "=" * 60)
if dependencias_ok:
    print("✅ TODAS LAS DEPENDENCIAS ESTÁN LISTAS")
    print("\nPuedes proceder a cargar PDFs en:")
    print("http://localhost:8000/ocr_validation/")
else:
    print("❌ FALTAN ALGUNAS DEPENDENCIAS")
    print("\nSigue las instrucciones anteriores para completar la instalación.")
print("=" * 60)

sys.exit(0 if dependencias_ok else 1)
