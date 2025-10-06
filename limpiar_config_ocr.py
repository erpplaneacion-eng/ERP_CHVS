#!/usr/bin/env python
"""
Script para limpiar y recrear la configuración OCR después de la migración.
Ejecutar desde la raíz del proyecto: python limpiar_config_ocr.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'erp_chvs'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from ocr_validation.models import OCRConfiguration

def limpiar_y_recrear():
    """Elimina configuraciones antiguas y crea una nueva con los valores correctos."""

    print("🧹 Limpiando configuraciones OCR antiguas...")

    # Eliminar todas las configuraciones
    count = OCRConfiguration.objects.all().count()
    OCRConfiguration.objects.all().delete()
    print(f"   ✅ Eliminadas {count} configuraciones antiguas")

    print("\n📝 Creando nueva configuración OCR...")

    # Crear nueva configuración con valores correctos
    config = OCRConfiguration.objects.create(
        modelo_landingai='dpt-2-latest',
        confianza_minima=90.0,
        tolerancia_posicion_x=5.0,
        tolerancia_posicion_y=5.0,
        permitir_texto_parcial=False,
        detectar_firmas=True,
        procesar_imagenes=True,
        guardar_imagenes_temporales=False
    )

    print(f"   ✅ Configuración creada con ID: {config.id}")
    print(f"   📊 Modelo LandingAI: {config.modelo_landingai}")
    print(f"   📊 Confianza mínima: {config.confianza_minima}%")
    print(f"   📊 Detectar firmas: {config.detectar_firmas}")
    print(f"   📊 Procesar imágenes: {config.procesar_imagenes}")

    print("\n✅ Configuración OCR lista para usar")
    print("   Ahora puedes reiniciar el servidor Django")

    return config

if __name__ == '__main__':
    try:
        limpiar_y_recrear()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
