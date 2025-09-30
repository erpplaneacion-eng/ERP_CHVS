"""
Script para buscar automáticamente la instalación de Tesseract en Windows.
"""

import os
import subprocess
import platform

def buscar_tesseract():
    """Busca Tesseract en todo el sistema Windows."""

    if platform.system() != 'Windows':
        print("❌ Este script es solo para Windows")
        return None

    print("🔍 Buscando Tesseract en el sistema...")

    # Método 1: Usar where para buscar en PATH
    try:
        resultado = subprocess.run(['where', 'tesseract'], capture_output=True, text=True)
        if resultado.returncode == 0:
            ruta = resultado.stdout.strip()
            print(f"✅ Tesseract encontrado en PATH: {ruta}")
            return ruta
    except:
        pass

    # Método 2: Buscar en rutas comunes
    rutas_comunes = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe',
        r'D:\Tesseract-OCR\tesseract.exe',
        r'E:\Tesseract-OCR\tesseract.exe',
        r'F:\Tesseract-OCR\tesseract.exe'
    ]

    for ruta in rutas_comunes:
        if os.path.exists(ruta):
            print(f"✅ Tesseract encontrado: {ruta}")
            return ruta

    # Método 3: Buscar en todas las unidades
    print("🔍 Buscando en todas las unidades de disco...")

    for letra in 'CDEFGH':
        ruta_base = f'{letra}:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        if os.path.exists(ruta_base):
            print(f"✅ Tesseract encontrado: {ruta_base}")
            return ruta_base

        ruta_base_alt = f'{letra}:\\Tesseract-OCR\\tesseract.exe'
        if os.path.exists(ruta_base_alt):
            print(f"✅ Tesseract encontrado: {ruta_base_alt}")
            return ruta_base_alt

    print("❌ Tesseract no encontrado en el sistema")
    return None

def verificar_tesseract(ruta_tesseract):
    """Verifica que Tesseract funciona correctamente."""

    if not ruta_tesseract:
        return False

    try:
        # Ejecutar tesseract para verificar que funciona
        resultado = subprocess.run([ruta_tesseract, '--version'],
                                 capture_output=True, text=True)

        if resultado.returncode == 0:
            print(f"✅ Tesseract funcionando correctamente: {resultado.stdout.strip()}")
            return True
        else:
            print(f"❌ Error ejecutando Tesseract: {resultado.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error verificando Tesseract: {e}")
        return False

def crear_configuracion(ruta_tesseract):
    """Crea archivo de configuración con la ruta encontrada."""

    config_content = f'''# Configuracion automatica de Tesseract
import pytesseract

# Ruta encontrada automaticamente
pytesseract.pytesseract.tesseract_cmd = r'{ruta_tesseract}'

print("Tesseract configurado desde: {ruta_tesseract}")
'''

    with open('tesseract_config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)

    print("✅ Archivo de configuración creado: tesseract_config.py")
    print("\n💡 Para usar en tu código:")
    print("   import tesseract_config")
    print("   # O copia la configuración directamente")

if __name__ == "__main__":
    print("🔍 Buscador automático de Tesseract para Windows")
    print("=" * 50)

    # Buscar Tesseract
    ruta_encontrada = buscar_tesseract()

    if ruta_encontrada:
        # Verificar que funciona
        if verificar_tesseract(ruta_encontrada):
            # Crear configuración
            crear_configuracion(ruta_encontrada)
            print("\n🎉 ¡Tesseract configurado exitosamente!")
        else:
            print("\n❌ Tesseract encontrado pero no funciona correctamente")
    else:
        print("\n❌ No se pudo encontrar Tesseract")
        print("\n💡 Soluciones:")
        print("1. Reinstalar Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Verificar que la instalación se completó correctamente")
        print("3. Buscar manualmente tesseract.exe en el Explorador")