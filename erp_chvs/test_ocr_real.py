#!/usr/bin/env python
"""
Script para probar el procesamiento OCR con un PDF real.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from ocr_validation.services import OCROrchestrator
import json


def test_procesar_pdf():
    """Prueba el procesamiento del PDF real."""

    # Ruta al PDF de prueba
    pdf_path = "ocr_validation/pdf ocr_organized.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ No se encontró el archivo: {pdf_path}")
        return False

    print("="*80)
    print("🧪 PRUEBA DE PROCESAMIENTO OCR")
    print("="*80)
    print(f"📄 Archivo: {pdf_path}")
    print(f"📊 Tamaño: {os.path.getsize(pdf_path) / 1024:.2f} KB")
    print("="*80)

    try:
        # Leer el archivo PDF
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        # Crear un UploadedFile simulado
        uploaded_file = SimpleUploadedFile(
            name="pdf_ocr_organized.pdf",
            content=pdf_content,
            content_type="application/pdf"
        )

        print("\n🚀 Iniciando procesamiento OCR...\n")

        # Crear orquestador y procesar
        orchestrator = OCROrchestrator()
        resultado = orchestrator.process_pdf(uploaded_file, usuario=None)

        print("\n" + "="*80)
        print("📊 RESULTADOS DEL PROCESAMIENTO")
        print("="*80)

        if resultado['success']:
            print(f"✅ Estado: EXITOSO")
            print(f"🆔 ID Validación: {resultado.get('validacion_id')}")
            print(f"⏱️  Tiempo: {resultado.get('tiempo_procesamiento', 0):.2f}s")
            print(f"🏫 Sede Educativa: {resultado.get('sede_educativa')}")
            print(f"❌ Total Errores: {resultado.get('total_errores', 0)}")

            # Mostrar errores por severidad
            errores = resultado.get('errores', [])

            criticos = [e for e in errores if e.get('severidad') == 'critico']
            advertencias = [e for e in errores if e.get('severidad') == 'advertencia']
            info = [e for e in errores if e.get('severidad') == 'info']

            print(f"\n📋 Desglose de errores:")
            print(f"   🔴 Críticos: {len(criticos)}")
            print(f"   🟡 Advertencias: {len(advertencias)}")
            print(f"   🔵 Info: {len(info)}")

            # Mostrar primeros 10 errores críticos
            if criticos:
                print(f"\n🔴 Errores Críticos (primeros 10):")
                for i, error in enumerate(criticos[:10], 1):
                    print(f"   {i}. [{error.get('tipo')}] {error.get('descripcion')}")
                    print(f"      Página: {error.get('pagina')}, Campo: {error.get('campo')}")

            # Mostrar primeras 5 advertencias
            if advertencias:
                print(f"\n🟡 Advertencias (primeras 5):")
                for i, error in enumerate(advertencias[:5], 1):
                    print(f"   {i}. [{error.get('tipo')}] {error.get('descripcion')}")

            # Guardar resultado completo en JSON
            output_file = "resultado_ocr_test.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n💾 Resultado completo guardado en: {output_file}")

        else:
            print(f"❌ Estado: ERROR")
            print(f"⚠️  Error: {resultado.get('error')}")
            print(f"⏱️  Tiempo: {resultado.get('tiempo_procesamiento', 0):.2f}s")

        print("="*80)

        return resultado['success']

    except Exception as e:
        print(f"\n💥 Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n")
    exito = test_procesar_pdf()
    print("\n")

    if exito:
        print("✅ Prueba completada exitosamente")
        sys.exit(0)
    else:
        print("❌ Prueba falló")
        sys.exit(1)
