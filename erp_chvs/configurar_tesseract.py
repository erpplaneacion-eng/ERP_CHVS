"""
Script para configurar Tesseract automáticamente en Windows.
"""

import os
import sys
import platform

def configurar_tesseract():
    """Configura automáticamente la ruta de Tesseract para Windows."""

    if platform.system() != 'Windows':
        print("❌ Este script es solo para Windows")
        return False

    print("🔧 Configurando Tesseract para Windows...")

    # Rutas comunes de instalación de Tesseract
    rutas_posibles = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe',
        r'D:\Tesseract-OCR\tesseract.exe',
        r'E:\Tesseract-OCR\tesseract.exe'
    ]

    tesseract_encontrado = None

    # Buscar Tesseract en rutas comunes
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            tesseract_encontrado = ruta
            print(f"✅ Tesseract encontrado: {ruta}")
            break

    if not tesseract_encontrado:
        print("❌ Tesseract no encontrado en rutas estándar")
        print("\n💡 Posibles soluciones:")
        print("1. Reinstalar Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Verificar que la instalación se completó correctamente")
        print("3. Buscar tesseract.exe en el Explorador de Windows")
        return False

    # Crear archivo de configuración
    config_content = f'''
# Configuracion automatica de Tesseract para Windows
import pytesseract

# Configurar ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'{tesseract_encontrado}'

print("Tesseract configurado automaticamente")
'''

    # Guardar configuración
    with open('config_tesseract.py', 'w') as f:
        f.write(config_content)

    print("✅ Archivo de configuración creado: config_tesseract.py")
    print("\n🚀 Para usar Tesseract en tu código, agrega:")
    print("   import config_tesseract")
    print("   # O copia la configuración directamente en tu código")

    return True

if __name__ == "__main__":
    configurar_tesseract()