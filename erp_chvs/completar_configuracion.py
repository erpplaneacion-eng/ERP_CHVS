"""
Script para completar la configuración del sistema OCR.
"""

import os

def completar_configuracion():
    """Completa la configuración del sistema OCR."""

    print("🚀 Completando configuración del sistema OCR...")

    # Ruta de Tesseract encontrada
    ruta_tesseract = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    if not os.path.exists(ruta_tesseract):
        print(f"❌ Tesseract no encontrado en: {ruta_tesseract}")
        print("💡 Ejecute primero: python buscar_tesseract.py")
        return False

    print(f"✅ Tesseract encontrado: {ruta_tesseract}")

    # Actualizar configuración en ocr_service.py
    try:
        # Leer archivo actual
        with open('ocr_validation/ocr_service.py', 'r', encoding='utf-8') as f:
            contenido = f.read()

        # Reemplazar ruta por defecto
        contenido_nuevo = contenido.replace(
            'ruta_defecto = r\'C:\\Program Files\\Tesseract-OCR\\tesseract.exe\'',
            f'ruta_tesseract = r\'{ruta_tesseract}\''
        )

        # Guardar cambios
        with open('ocr_validation/ocr_service.py', 'w', encoding='utf-8') as f:
            f.write(contenido_nuevo)

        print("✅ Archivo ocr_service.py actualizado con ruta correcta")

    except Exception as e:
        print(f"❌ Error actualizando configuración: {e}")
        return False

    # Crear archivo de configuración simple
    config_simple = f'''# Configuracion de Tesseract
import pytesseract

# Ruta de Tesseract en este sistema
pytesseract.pytesseract.tesseract_cmd = r'{ruta_tesseract}'

print("Tesseract configurado correctamente")
'''

    with open('tesseract_config.py', 'w', encoding='utf-8') as f:
        f.write(config_simple)

    print("✅ Archivo tesseract_config.py creado")

    return True

if __name__ == "__main__":
    if completar_configuracion():
        print("\n🎉 ¡Configuración completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Crear migraciones: python manage.py makemigrations ocr_validation")
        print("2. Aplicar migraciones: python manage.py migrate")
        print("3. Verificar sistema: python verificar_sistema.py")
        print("4. Usar el sistema desde el dashboard de facturación")
    else:
        print("\n❌ No se pudo completar la configuración")
        print("💡 Ejecute primero: python buscar_tesseract.py")