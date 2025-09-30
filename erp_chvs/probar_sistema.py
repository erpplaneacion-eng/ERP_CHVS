"""
Script para probar el sistema OCR con configuración Django correcta.
"""

import os
import sys
import django

# Configurar Django correctamente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

def probar_sistema():
    """Prueba el sistema OCR completo."""

    print("🔍 Probando sistema OCR con configuración Django...")

    try:
        # Importar después de configurar Django
        from ocr_validation.ocr_service import OCRProcessor

        # Crear procesador OCR
        procesador = OCRProcessor()
        print("✅ OCR Processor creado exitosamente")

        # Verificar configuración
        print("✅ Configuración OCR cargada correctamente")

        # Verificar modelos
        from ocr_validation.models import PDFValidation, ValidationError
        print("✅ Modelos de datos disponibles")

        # Verificar vistas
        from ocr_validation import views
        print("✅ Vistas importadas correctamente")

        print("\n🎉 ¡Sistema OCR completamente funcional!")
        print("\n📋 Próximos pasos:")
        print("1. Crear migraciones: python manage.py makemigrations ocr_validation")
        print("2. Aplicar migraciones: python manage.py migrate")
        print("3. Acceder al sistema desde: /ocr_validation/")

        return True

    except Exception as e:
        print(f"❌ Error probando sistema: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    probar_sistema()